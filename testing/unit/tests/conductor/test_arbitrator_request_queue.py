"""Serial request queue — spec §7.4 deadlock prevention.

The arbitrator enforces: at most one root-level request in_flight per
session. Child requests (parent_request_id non-null) bypass the queue
so handlers can fan out without deadlocking on themselves.

These tests drive the queue API directly, no conductor.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from services.conductor.arbitrator import (
    Arbitrator,
    RequestStatus,
)


@pytest.fixture
def queue_arb(arb_factory, run_async):
    """A connected arbitrator with one session opened and a handler registered."""
    arb: Arbitrator = arb_factory()

    async def _setup():
        await arb.start()
        sid = uuid4()
        await arb.open_session(sid, initial_team_id="caller")
        arb.register_request_kind("k.x", input_schema={}, response_schema={})
        arb.register_request_handler("responder", "k.x", "handler")
        return sid

    sid = run_async(_setup())
    yield arb, sid

    async def _tear():
        await arb.close()

    run_async(_tear())


def test_single_root_request_goes_in_flight(queue_arb, run_async):
    arb, sid = queue_arb

    async def _t():
        req = await arb.create_request(
            session_id=sid,
            from_team="caller",
            to_team="responder",
            kind="k.x",
            input_data={},
        )
        ready = await arb.next_ready_request(sid)
        assert ready is not None
        assert ready.request_id == req.request_id
        assert ready.status == RequestStatus.IN_FLIGHT

    run_async(_t())


def test_second_root_blocks_until_first_completes(queue_arb, run_async):
    arb, sid = queue_arb

    async def _t():
        r1 = await arb.create_request(
            session_id=sid,
            from_team="caller",
            to_team="responder",
            kind="k.x",
            input_data={"i": 1},
        )
        r2 = await arb.create_request(
            session_id=sid,
            from_team="caller",
            to_team="responder",
            kind="k.x",
            input_data={"i": 2},
        )
        # First pull: r1.
        first = await arb.next_ready_request(sid)
        assert first.request_id == r1.request_id
        # Second pull while r1 is in-flight: blocked.
        blocked = await arb.next_ready_request(sid)
        assert blocked is None
        # Complete r1. Now r2 is ready.
        await arb.complete_request(r1.request_id, response={"ok": 1})
        second = await arb.next_ready_request(sid)
        assert second is not None
        assert second.request_id == r2.request_id

    run_async(_t())


def test_child_request_bypasses_root_queue(queue_arb, run_async):
    """A child request (non-null parent_request_id) bypasses the serial queue."""
    arb, sid = queue_arb

    async def _t():
        root = await arb.create_request(
            session_id=sid,
            from_team="caller",
            to_team="responder",
            kind="k.x",
            input_data={"root": True},
        )
        # Root goes in-flight.
        first = await arb.next_ready_request(sid)
        assert first.request_id == root.request_id

        # While root is in-flight, create a CHILD request from within the handler.
        child = await arb.create_request(
            session_id=sid,
            from_team="responder",
            to_team="responder",
            kind="k.x",
            input_data={"child": True},
            parent_request_id=root.request_id,
        )
        # Child bypasses the queue — next_ready_request returns it immediately.
        pulled = await arb.next_ready_request(sid)
        assert pulled is not None
        assert pulled.request_id == child.request_id
        assert pulled.parent_request_id == root.request_id

    run_async(_t())


def test_children_advance_while_root_holds_queue(queue_arb, run_async):
    arb, sid = queue_arb

    async def _t():
        # Three roots: r1, r2, r3. Two children on r1: c1a, c1b.
        r1 = await arb.create_request(
            sid, "caller", "responder", "k.x", {"r": 1}
        )
        r2 = await arb.create_request(
            sid, "caller", "responder", "k.x", {"r": 2}
        )
        r3 = await arb.create_request(
            sid, "caller", "responder", "k.x", {"r": 3}
        )

        # r1 in-flight.
        pulled = await arb.next_ready_request(sid)
        assert pulled.request_id == r1.request_id

        c1a = await arb.create_request(
            sid,
            "responder",
            "responder",
            "k.x",
            {},
            parent_request_id=r1.request_id,
        )
        c1b = await arb.create_request(
            sid,
            "responder",
            "responder",
            "k.x",
            {},
            parent_request_id=r1.request_id,
        )

        # Children advance in FIFO order even though r1 holds the root slot.
        nx1 = await arb.next_ready_request(sid)
        nx2 = await arb.next_ready_request(sid)
        pulled_ids = {nx1.request_id, nx2.request_id}
        assert pulled_ids == {c1a.request_id, c1b.request_id}

        # r2, r3 still blocked.
        blocked = await arb.next_ready_request(sid)
        assert blocked is None

        # Complete children, then r1. r2 should now advance.
        await arb.complete_request(c1a.request_id, response={})
        await arb.complete_request(c1b.request_id, response={})
        await arb.complete_request(r1.request_id, response={})
        nxt = await arb.next_ready_request(sid)
        assert nxt.request_id == r2.request_id

    run_async(_t())


def test_next_ready_returns_none_when_empty(queue_arb, run_async):
    arb, sid = queue_arb

    async def _t():
        result = await arb.next_ready_request(sid)
        assert result is None

    run_async(_t())


def test_timeout_status_frees_the_queue(queue_arb, run_async):
    arb, sid = queue_arb

    async def _t():
        r1 = await arb.create_request(
            sid, "caller", "responder", "k.x", {}
        )
        r2 = await arb.create_request(
            sid, "caller", "responder", "k.x", {}
        )
        first = await arb.next_ready_request(sid)
        assert first.request_id == r1.request_id

        # Timeout r1 — should free the slot for r2.
        await arb.complete_request(
            r1.request_id, response={}, status=RequestStatus.TIMEOUT
        )
        second = await arb.next_ready_request(sid)
        assert second is not None
        assert second.request_id == r2.request_id

    run_async(_t())


def test_fifo_ordering_under_back_to_back_enqueue(queue_arb, run_async):
    arb, sid = queue_arb

    async def _t():
        reqs = []
        for i in range(10):
            reqs.append(
                await arb.create_request(
                    sid, "caller", "responder", "k.x", {"i": i}
                )
            )
        # Drain in order by completing each before pulling the next.
        order = []
        for _ in range(10):
            pulled = await arb.next_ready_request(sid)
            assert pulled is not None
            order.append(pulled.request_id)
            await arb.complete_request(pulled.request_id, response={})
        assert order == [r.request_id for r in reqs]

    run_async(_t())
