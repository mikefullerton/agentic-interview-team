"""Integration surface test fixtures.

`transport_factory` is parametrized over every available transport. Any
new transport (stdio, WebSocket, …) registers itself here so the full
`contract/` suite runs against it.
"""
from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import AsyncIterator, Callable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))

from services.integration_surface import (  # noqa: E402
    InProcessSession,
    StdioSession,
    TeamSession,
)

from .fixtures.fake_team import FakeTeam  # noqa: E402


@pytest.fixture
def run_async():
    def runner(coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    return runner


def _serialize_fake(fake: FakeTeam) -> dict:
    """Serialize a FakeTeam's scripted replies into JSON that the stdio
    harness reconstructs in the subprocess. Only the default
    (always-match) matcher is supported — tests that need custom
    matchers must stay in-process."""
    replies = []
    for r in fake._replies:
        replies.append(
            {
                "events": [list(ev) for ev in r.events],
                "ask": list(r.ask) if r.ask is not None else None,
                "after_answer": [list(ev) for ev in r.after_answer],
            }
        )
    return {"replies": replies}


_STDIO_ENTRY = (
    REPO_ROOT
    / "testing"
    / "unit"
    / "tests"
    / "integration_surface"
    / "fixtures"
    / "stdio_server.py"
)


def _stdio_factory(runner) -> TeamSession:
    if not isinstance(runner, FakeTeam):
        pytest.skip("stdio transport factory only supports FakeTeam scripts")
    script = json.dumps(_serialize_fake(runner))
    return StdioSession(
        cmd=[sys.executable, str(_STDIO_ENTRY)],
        env={"AGENTIC_FAKE_SCRIPT": script, "PYTHONUNBUFFERED": "1"},
    )


@pytest.fixture(params=["in_process", "stdio"])
def transport_factory(request) -> Callable[[object], TeamSession]:
    """Returns a factory callable: (runner) -> TeamSession."""
    kind = request.param
    if kind == "in_process":
        return lambda runner: InProcessSession(runner)
    if kind == "stdio":
        return _stdio_factory
    raise AssertionError(f"unknown transport: {kind}")


@pytest.fixture
def collect_events():
    """Helper: consume `events(session_id)` until a terminator.

    Accepts either a single event type ("result") or a sentinel function.
    """
    async def _collect(
        session: TeamSession,
        session_id: str,
        until_type: str = "result",
    ) -> list:
        out = []
        async for ev in session.events(session_id):
            out.append(ev)
            if ev.type == until_type:
                return out
        return out

    return _collect
