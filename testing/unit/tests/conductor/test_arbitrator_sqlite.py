"""Arbitrator + SqliteBackend smoke tests."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))

from services.conductor.arbitrator import (  # noqa: E402
    Arbitrator,
    RequestStatus,
    SessionStatus,
    TaskStatus,
)
from services.conductor.arbitrator.backends import SqliteBackend  # noqa: E402
from services.conductor.arbitrator.models import StateStatus  # noqa: E402


@pytest.fixture
def arb_factory(tmp_path):
    def _factory():
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        return Arbitrator(backend)

    return _factory


def run(coro):
    return asyncio.run(coro)


def test_open_and_close_session(arb_factory):
    async def _t():
        arb = arb_factory()
        await arb.start()
        sid = uuid4()
        session = await arb.open_session(sid, "name-a-puppy")
        assert session.status == SessionStatus.OPEN
        # Idempotent re-open
        session2 = await arb.open_session(sid, "name-a-puppy")
        assert session2.session_id == sid
        await arb.close_session(sid, SessionStatus.COMPLETED)
        await arb.close()

    run(_t())


def test_message_and_result_round_trip(arb_factory):
    async def _t():
        arb = arb_factory()
        await arb.start()
        sid = uuid4()
        await arb.open_session(sid, "name-a-puppy")
        await arb.create_message(sid, "name-a-puppy", "out", "notification", "hi")
        msgs = await arb.list_messages(sid)
        assert len(msgs) == 1 and msgs[0].body == "hi"
        result = await arb.create_result(
            sid, "name-a-puppy", "breed", True, {"candidates": ["Luna"]}
        )
        await arb.create_finding(result.result_id, "suggestion", "info", "Luna")
        results = await arb.list_results(sid)
        assert len(results) == 1 and results[0].passed is True
        await arb.close()

    run(_t())


def test_state_tree_push_pop(arb_factory):
    async def _t():
        arb = arb_factory()
        await arb.start()
        sid = uuid4()
        await arb.open_session(sid, "name-a-puppy")
        root = await arb.push_state(sid, "name-a-puppy", "start", None)
        child = await arb.push_state(sid, "name-a-puppy", "gather", root.node_id)
        active = await arb.active_state_nodes(sid)
        assert {n.node_id for n in active} == {root.node_id, child.node_id}
        await arb.pop_state(child.node_id)
        await arb.pop_state(root.node_id)
        active_after = await arb.active_state_nodes(sid)
        assert active_after == []
        await arb.close()

    run(_t())


def test_task_queue(arb_factory):
    async def _t():
        arb = arb_factory()
        await arb.start()
        sid = uuid4()
        await arb.open_session(sid, "name-a-puppy")
        t1 = await arb.enqueue_task(sid, "name-a-puppy", "tick", {"n": 1})
        t2 = await arb.enqueue_task(sid, "name-a-puppy", "tick", {"n": 2})
        first = await arb.next_task(sid)
        assert first is not None and first.task_id == t1.task_id
        assert first.status == TaskStatus.IN_PROGRESS
        await arb.complete_task(first.task_id, {"ok": True})
        second = await arb.next_task(sid)
        assert second is not None and second.task_id == t2.task_id
        third = await arb.next_task(sid)  # only in_progress remains
        assert third is None
        await arb.close()

    run(_t())


def test_events_ordered_by_sequence(arb_factory):
    async def _t():
        arb = arb_factory()
        await arb.start()
        sid = uuid4()
        await arb.open_session(sid, "name-a-puppy")
        for i in range(5):
            await arb.emit_event(sid, "name-a-puppy", "tick", {"i": i})
        evs = await arb.list_events(sid)
        assert [e.sequence for e in evs] == [1, 2, 3, 4, 5]
        tail = await arb.list_events(sid, since_sequence=3)
        assert [e.sequence for e in tail] == [4, 5]
        await arb.close()

    run(_t())


def test_request_serial_queue(arb_factory):
    async def _t():
        arb = arb_factory()
        await arb.start()
        sid = uuid4()
        await arb.open_session(sid, "pm")
        arb.register_request_kind(
            "pm.schedule.create", {}, {}, default_timeout_seconds=60
        )
        arb.register_request_handler("pm", "pm.schedule.create", "handle_create")
        r1 = await arb.create_request(sid, "dev", "pm", "pm.schedule.create", {})
        r2 = await arb.create_request(sid, "dev", "pm", "pm.schedule.create", {})
        # First pull: r1 goes in-flight.
        ready = await arb.next_ready_request(sid)
        assert ready is not None and ready.request_id == r1.request_id
        # r2 is blocked by the serial queue.
        blocked = await arb.next_ready_request(sid)
        assert blocked is None
        await arb.complete_request(r1.request_id, {"ok": True})
        ready2 = await arb.next_ready_request(sid)
        assert ready2 is not None and ready2.request_id == r2.request_id
        await arb.close()

    run(_t())


def test_state_node_completed_status(arb_factory):
    async def _t():
        arb = arb_factory()
        await arb.start()
        sid = uuid4()
        await arb.open_session(sid, "t")
        n = await arb.push_state(sid, "t", "s", None)
        await arb.pop_state(n.node_id, StateStatus.COMPLETED)
        await arb.close()

    run(_t())
