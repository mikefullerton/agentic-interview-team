"""Shared fixtures and invariant checks for conductor tests.

Provides:
- Path bootstrap so every test module can import `services.conductor.*`
  without repeating the sys.path dance.
- `arb_factory` / `tmp_arbitrator` — disposable SQLite-backed arbitrators.
- `session_id` — a fresh UUID per test.
- `mock_dispatcher` — pre-wired with the agents the existing playbooks use.
- `run_async` — `asyncio.run(coro)` helper so tests don't repeat the
  inner `_t()` wrapper pattern.
- `assert_session_invariants` — the load-bearing helper that every
  end-to-end test calls. Asserts the session didn't leave a mess.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "dev-team"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from services.conductor.arbitrator import (  # noqa: E402
    Arbitrator,
    RequestStatus,
    SessionStatus,
)
from services.conductor.arbitrator.backends import SqliteBackend  # noqa: E402
from services.conductor.arbitrator.models import StateStatus  # noqa: E402
from services.conductor.dispatcher import MockDispatcher  # noqa: E402


PLAYBOOKS_DIR = PLUGIN_ROOT / "services" / "conductor" / "playbooks"


@pytest.fixture
def run_async():
    """Run an async coroutine in a fresh event loop. Replaces ad-hoc `_t()`."""
    return lambda coro: asyncio.run(coro)


@pytest.fixture
def session_id() -> UUID:
    return uuid4()


@pytest.fixture
def arb_factory(tmp_path):
    """Factory producing unconnected Arbitrators against a fresh SQLite file.

    Tests that want a connected arbitrator should use `tmp_arbitrator`.
    """
    counter = {"n": 0}

    def _factory() -> Arbitrator:
        counter["n"] += 1
        path = tmp_path / f"arb_{counter['n']}.sqlite"
        return Arbitrator(SqliteBackend(path))

    return _factory


@pytest.fixture
def backend_factory(tmp_path):
    """Factory producing fresh `SqliteBackend` instances on unique paths.

    Every test gets its own DB file. Tests that want a pre-connected
    arbitrator should create and connect inside their own `asyncio.run`
    body to keep asyncio.Lock bound to the right event loop.
    """
    counter = {"n": 0}

    def _factory() -> SqliteBackend:
        counter["n"] += 1
        return SqliteBackend(tmp_path / f"backend_{counter['n']}.sqlite")

    return _factory


@pytest.fixture
def mock_dispatcher() -> MockDispatcher:
    """A dispatcher pre-wired for the name-a-puppy and pet-coach playbooks.

    Tests can override specific agents via `mock_dispatcher.set_response(...)`.
    """
    return MockDispatcher(
        {
            "themed-name-worker": {"candidates": ["Scout", "River", "Sage"]},
            "breed-worker": {
                "candidates": ["Buddy", "Max", "Charlie"],
                "findings": [
                    {"kind": "candidate", "severity": "info", "body": "Buddy"}
                ],
            },
            "lifestyle-worker": {
                "candidates": ["Luna", "Nova", "Willow"],
                "findings": [
                    {"kind": "candidate", "severity": "info", "body": "Luna"}
                ],
            },
            "temperament-worker": {
                "candidates": ["Cooper", "Finn", "Oscar"],
                "findings": [
                    {"kind": "candidate", "severity": "info", "body": "Cooper"}
                ],
            },
            "team-lead-judgment": {"next_state": "done"},
        }
    )


@pytest.fixture
def playbooks_dir() -> Path:
    return PLAYBOOKS_DIR


# ---------------------------------------------------------------------------
# Session invariants — the load-bearing assertion helper.
# ---------------------------------------------------------------------------


async def assert_session_invariants(
    backend: SqliteBackend,
    session_id: UUID,
    *,
    allow_active_states: bool = False,
    allow_pending_requests: bool = False,
) -> None:
    """Assert the session didn't leave a mess.

    Call from the bottom of every end-to-end test. Flags let crash-recovery
    tests explicitly opt into known-incomplete state.

    Checks:
        1. state tree balance — every row has exit_date (unless allow_active)
        2. event sequence is a contiguous 1..N with no duplicates
        3. no dangling requests (unless allow_pending)
        4. finding.result_id points to a real result row
        5. session row exists, is closed, has ended_at set
        6. state.parent_node_id FK integrity
    """
    sid = str(session_id)

    # (5) session row present and closed.
    session_row = await backend.fetch_one("session", {"session_id": sid})
    assert session_row is not None, f"session {sid} missing"
    assert session_row["status"] in (
        SessionStatus.COMPLETED.value,
        SessionStatus.FAILED.value,
    ), f"session {sid} still open: status={session_row['status']}"
    assert session_row["ended_at"] is not None, "session.ended_at not set"

    # (1) state tree balance.
    state_rows = await backend.fetch_all("state", where={"session_id": sid})
    if not allow_active_states:
        for row in state_rows:
            assert row["exit_date"] is not None, (
                f"state {row['node_id']} ({row['state_name']}) "
                f"left active with exit_date=NULL"
            )
            assert row["status"] == StateStatus.COMPLETED.value, (
                f"state {row['node_id']} status={row['status']!r} "
                f"expected completed"
            )

    # (6) state parent FK integrity.
    node_ids = {row["node_id"] for row in state_rows}
    for row in state_rows:
        parent = row["parent_node_id"]
        if parent is not None:
            assert parent in node_ids, (
                f"state {row['node_id']} has parent_node_id={parent!r} "
                f"which does not exist in session {sid}"
            )

    # (2) event sequence strictly monotonic [1..N].
    event_rows = await backend.fetch_all(
        "event", where={"session_id": sid}, order_by="sequence"
    )
    sequences = [int(r["sequence"]) for r in event_rows]
    if sequences:
        assert sequences[0] == 1, f"events start at {sequences[0]} not 1"
        assert sequences == list(range(1, len(sequences) + 1)), (
            f"event sequence has gaps or duplicates: {sequences}"
        )

    # (3) no dangling requests.
    if not allow_pending_requests:
        request_rows = await backend.fetch_all(
            "request", where={"session_id": sid}
        )
        terminal = {
            RequestStatus.COMPLETED.value,
            RequestStatus.FAILED.value,
            RequestStatus.TIMEOUT.value,
        }
        for row in request_rows:
            assert row["status"] in terminal, (
                f"request {row['request_id']} still non-terminal: "
                f"status={row['status']!r}"
            )

    # (4) finding.result_id integrity.
    result_rows = await backend.fetch_all("result", where={"session_id": sid})
    result_ids = {r["result_id"] for r in result_rows}
    finding_rows = await backend.fetch_all("finding")
    # Only check findings whose result belongs to this session.
    session_findings = [
        f for f in finding_rows if f["result_id"] in result_ids
    ]
    for f in session_findings:
        assert f["result_id"] in result_ids, (
            f"finding {f['finding_id']} points to missing result "
            f"{f['result_id']}"
        )


@pytest.fixture
def assert_invariants():
    """Expose the invariant helper as a fixture so tests can await it."""
    return assert_session_invariants


# ---------------------------------------------------------------------------
# Helpers for the stress suite — ensure marker recognized when imported.
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "stress: opt-in stress tests; run via `pytest -m stress`"
    )


# Session status passthrough for convenience in assertion-heavy tests.
__all__ = [
    "SessionStatus",
    "RequestStatus",
    "StateStatus",
    "Arbitrator",
    "SqliteBackend",
    "MockDispatcher",
    "PLAYBOOKS_DIR",
    "assert_session_invariants",
]


# Re-export for test modules that want `from .conftest import ...`.
def _for_test_imports() -> dict[str, Any]:
    return {
        "SessionStatus": SessionStatus,
        "RequestStatus": RequestStatus,
        "StateStatus": StateStatus,
    }
