"""Arbitrator invariants — duplicate keys, nullable columns, sequencing.

Targets the contract guarantees of the arbitrator API, not end-to-end
behavior. If one of these breaks, every session-level test will fail
in a confusing way; catch it here first.
"""
from __future__ import annotations

import asyncio
import sqlite3

import pytest

from services.conductor.arbitrator import (
    Arbitrator,
    RequestStatus,
    SessionStatus,
)
from services.conductor.arbitrator.backends import SqliteBackend
from services.conductor.arbitrator.models import StateStatus


def test_duplicate_session_pk_is_idempotent(arb_factory, session_id, run_async):
    """open_session with the same UUID twice should return the existing row."""

    async def _t():
        arb: Arbitrator = arb_factory()
        await arb.start()
        first = await arb.open_session(session_id, initial_team_id="t1")
        second = await arb.open_session(session_id, initial_team_id="t2")
        assert first.session_id == second.session_id
        # The initial_team_id of the first write wins — idempotent.
        assert second.initial_team_id == "t1"
        await arb.close()

    run_async(_t())


def test_duplicate_state_pk_raises(arb_factory, session_id, run_async):
    """Manual duplicate state insertion hits the PK constraint."""

    async def _t():
        arb: Arbitrator = arb_factory()
        await arb.start()
        await arb.open_session(session_id, initial_team_id="t1")
        node = await arb.push_state(
            session_id=session_id,
            team_id="t1",
            state_name="s",
            parent_node_id=None,
        )
        # Re-inserting the same node_id must hit UNIQUE on PK.
        with pytest.raises(sqlite3.IntegrityError):
            await arb._storage.insert(  # noqa: SLF001
                "state",
                {
                    "node_id": node.node_id,
                    "session_id": str(session_id),
                    "team_id": "t1",
                    "parent_node_id": None,
                    "state_name": "s",
                    "status": StateStatus.ACTIVE.value,
                    "entered_at": "2026-04-11T00:00:00+00:00",
                    "exited_at": None,
                },
            )
        await arb.close()

    run_async(_t())


def test_optional_columns_round_trip_as_none(arb_factory, session_id, run_async):
    """Nullable columns written as None come back as None, not empty string."""

    async def _t():
        arb: Arbitrator = arb_factory()
        await arb.start()
        await arb.open_session(session_id, initial_team_id="t1")

        # State with no parent.
        node = await arb.push_state(
            session_id=session_id,
            team_id="t1",
            state_name="s",
            parent_node_id=None,
        )
        row = await arb._storage.fetch_one(  # noqa: SLF001
            "state", {"node_id": node.node_id}
        )
        assert row["parent_node_id"] is None
        assert row["exited_at"] is None

        # Finding with no source_artifact.
        result = await arb.create_result(
            session_id=session_id,
            team_id="t1",
            specialist_id="sp",
            passed=True,
            summary={},
        )
        finding = await arb.create_finding(
            result_id=result.result_id,
            kind="note",
            severity="info",
            body="hello",
        )
        frow = await arb._storage.fetch_one(  # noqa: SLF001
            "finding", {"finding_id": finding.finding_id}
        )
        assert frow["source_artifact"] is None

        await arb.close()

    run_async(_t())


def test_close_session_sets_ended_at_for_every_status(
    arb_factory, session_id, run_async
):
    async def _t():
        arb: Arbitrator = arb_factory()
        await arb.start()
        await arb.open_session(session_id, initial_team_id="t1")
        await arb.close_session(session_id, SessionStatus.FAILED)
        row = await arb._storage.fetch_one(  # noqa: SLF001
            "session", {"session_id": str(session_id)}
        )
        assert row["status"] == SessionStatus.FAILED.value
        assert row["ended_at"] is not None
        await arb.close()

    run_async(_t())


def test_event_sequence_resets_per_session(arb_factory, run_async):
    """Two sessions must each start their sequence at 1, independently."""
    from uuid import uuid4

    async def _t():
        arb: Arbitrator = arb_factory()
        await arb.start()
        sid_a = uuid4()
        sid_b = uuid4()
        await arb.open_session(sid_a, initial_team_id="t1")
        await arb.open_session(sid_b, initial_team_id="t1")

        for _ in range(3):
            await arb.emit_event(
                session_id=sid_a, team_id="t1", kind="k", payload={}
            )
        await arb.emit_event(
            session_id=sid_b, team_id="t1", kind="k", payload={}
        )

        events_a = await arb.list_events(sid_a)
        events_b = await arb.list_events(sid_b)

        assert [e.sequence for e in events_a] == [1, 2, 3]
        assert [e.sequence for e in events_b] == [1]

        await arb.close()

    run_async(_t())


def test_list_events_since_sequence_boundary(arb_factory, session_id, run_async):
    """list_events(since_sequence=N) must be strictly greater-than."""

    async def _t():
        arb: Arbitrator = arb_factory()
        await arb.start()
        await arb.open_session(session_id, initial_team_id="t1")
        for _ in range(5):
            await arb.emit_event(
                session_id=session_id, team_id="t1", kind="k", payload={}
            )

        all_evs = await arb.list_events(session_id)
        assert [e.sequence for e in all_evs] == [1, 2, 3, 4, 5]

        after_three = await arb.list_events(session_id, since_sequence=3)
        assert [e.sequence for e in after_three] == [4, 5]

        after_last = await arb.list_events(session_id, since_sequence=5)
        assert after_last == []

        await arb.close()

    run_async(_t())


def test_state_status_enum_matches_db(arb_factory, session_id, run_async):
    """The StateStatus enum values must be what the DB actually stores."""

    async def _t():
        arb: Arbitrator = arb_factory()
        await arb.start()
        await arb.open_session(session_id, initial_team_id="t1")
        node = await arb.push_state(
            session_id=session_id,
            team_id="t1",
            state_name="s",
            parent_node_id=None,
        )
        row = await arb._storage.fetch_one(  # noqa: SLF001
            "state", {"node_id": node.node_id}
        )
        assert row["status"] == StateStatus.ACTIVE.value == "active"

        await arb.pop_state(node.node_id, StateStatus.FAILED)
        row2 = await arb._storage.fetch_one(  # noqa: SLF001
            "state", {"node_id": node.node_id}
        )
        assert row2["status"] == StateStatus.FAILED.value == "failed"
        await arb.close()

    run_async(_t())


def test_request_pk_must_be_unique(arb_factory, session_id, run_async):
    async def _t():
        arb: Arbitrator = arb_factory()
        await arb.start()
        await arb.open_session(session_id, initial_team_id="t1")
        arb.register_request_kind(
            "k.test", input_schema={}, response_schema={}
        )
        arb.register_request_handler("t2", "k.test", "handler")
        req = await arb.create_request(
            session_id=session_id,
            from_team="t1",
            to_team="t2",
            kind="k.test",
            input_data={},
        )
        # Manual duplicate insert of the same request_id must hit PK constraint.
        with pytest.raises(sqlite3.IntegrityError):
            await arb._storage.insert(  # noqa: SLF001
                "request",
                {
                    "request_id": req.request_id,
                    "session_id": str(session_id),
                    "from_team": "t1",
                    "to_team": "t2",
                    "kind": "k.test",
                    "input_json": "{}",
                    "status": RequestStatus.PENDING.value,
                    "response_json": None,
                    "parent_request_id": None,
                    "enqueued_at": "2026-04-11T00:00:00+00:00",
                    "in_flight_at": None,
                    "completed_at": None,
                    "timeout_at": "2026-04-11T00:05:00+00:00",
                },
            )
        await arb.close()

    run_async(_t())
