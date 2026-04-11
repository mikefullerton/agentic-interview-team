"""Round-trip tests for every arbitrator resource schema (spec §13.1).

For each resource:
1. Create via the arbitrator API.
2. Fetch the raw row via the storage backend.
3. Assert every field that was written is present and correct.
4. Confirm the indexed columns are queryable via where= lookups.

The point of these tests is to catch schema drift. If someone adds or
renames a column in schema.sql without updating the API, the row-create
call or the field assertions will blow up here before any end-to-end
test has a chance to produce a confusing failure.
"""
from __future__ import annotations

import json
from uuid import uuid4

import pytest

from services.conductor.arbitrator import (
    Arbitrator,
    RequestStatus,
    SessionStatus,
    TaskStatus,
)


@pytest.fixture
def arb(arb_factory):
    return arb_factory()


def test_session_round_trip(arb, session_id, run_async):
    async def _t():
        await arb.start()
        await arb.open_session(
            session_id, initial_team_id="team-a", metadata={"k": "v"}
        )
        row = await arb._storage.fetch_one(  # noqa: SLF001
            "session", {"session_id": str(session_id)}
        )
        assert row["initial_team_id"] == "team-a"
        assert row["status"] == SessionStatus.OPEN.value
        assert json.loads(row["metadata_json"]) == {"k": "v"}
        await arb.close()

    run_async(_t())


def test_state_round_trip_and_index(arb, session_id, run_async):
    async def _t():
        await arb.start()
        await arb.open_session(session_id, initial_team_id="t")
        parent = await arb.push_state(session_id, "t", "parent", None)
        child = await arb.push_state(
            session_id, "t", "child", parent.node_id
        )
        # Indexed by (session_id, parent_node_id) — use the index.
        rows = await arb._storage.fetch_all(  # noqa: SLF001
            "state",
            where={
                "session_id": str(session_id),
                "parent_node_id": parent.node_id,
            },
        )
        assert len(rows) == 1
        assert rows[0]["node_id"] == child.node_id
        await arb.close()

    run_async(_t())


def test_message_round_trip(arb, session_id, run_async):
    async def _t():
        await arb.start()
        await arb.open_session(session_id, initial_team_id="t")
        msg = await arb.create_message(
            session_id=session_id,
            team_id="t",
            direction="out",
            type="notification",
            body="hi",
        )
        rows = await arb.list_messages(session_id)
        assert len(rows) == 1
        assert rows[0].message_id == msg.message_id
        assert rows[0].body == "hi"
        assert rows[0].direction == "out"
        assert rows[0].type == "notification"
        await arb.close()

    run_async(_t())


def test_gate_round_trip(arb, session_id, run_async):
    async def _t():
        await arb.start()
        await arb.open_session(session_id, initial_team_id="t")
        gate = await arb.create_gate(
            session_id=session_id,
            team_id="t",
            category="confirm",
            options=["a", "b"],
        )
        row = await arb._storage.fetch_one(  # noqa: SLF001
            "gate", {"gate_id": gate.gate_id}
        )
        assert json.loads(row["options_json"]) == ["a", "b"]
        assert row["verdict"] is None
        await arb.resolve_gate(gate.gate_id, "a")
        row2 = await arb._storage.fetch_one(  # noqa: SLF001
            "gate", {"gate_id": gate.gate_id}
        )
        assert row2["verdict"] == "a"
        assert row2["resolved_at"] is not None
        await arb.close()

    run_async(_t())


def test_result_and_finding_round_trip(arb, session_id, run_async):
    async def _t():
        await arb.start()
        await arb.open_session(session_id, initial_team_id="t")
        result = await arb.create_result(
            session_id=session_id,
            team_id="t",
            specialist_id="sp",
            passed=True,
            summary={"k": 1},
        )
        await arb.create_finding(
            result_id=result.result_id,
            kind="note",
            severity="info",
            body="finding body",
            source_artifact="a.txt",
        )
        results = await arb.list_results(session_id)
        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].summary_json == {"k": 1}
        findings = await arb._storage.fetch_all(  # noqa: SLF001
            "finding", where={"result_id": result.result_id}
        )
        assert len(findings) == 1
        assert findings[0]["body"] == "finding body"
        assert findings[0]["source_artifact"] == "a.txt"
        await arb.close()

    run_async(_t())


def test_event_round_trip_and_ordering(arb, session_id, run_async):
    async def _t():
        await arb.start()
        await arb.open_session(session_id, initial_team_id="t")
        e1 = await arb.emit_event(
            session_id=session_id, team_id="t", kind="k1", payload={"n": 1}
        )
        e2 = await arb.emit_event(
            session_id=session_id,
            team_id="t",
            kind="k2",
            payload={"n": 2},
            agent_id="agent-1",
            dispatch_id="d1",
        )
        evs = await arb.list_events(session_id)
        assert [e.event_id for e in evs] == [e1.event_id, e2.event_id]
        assert evs[1].agent_id == "agent-1"
        assert evs[1].dispatch_id == "d1"
        assert evs[1].payload_json == {"n": 2}
        await arb.close()

    run_async(_t())


def test_task_round_trip_and_queue_order(arb, session_id, run_async):
    async def _t():
        await arb.start()
        await arb.open_session(session_id, initial_team_id="t")
        t1 = await arb.enqueue_task(session_id, "t", "k", {"i": 1})
        t2 = await arb.enqueue_task(session_id, "t", "k", {"i": 2})
        next1 = await arb.next_task(session_id)
        assert next1.task_id == t1.task_id
        assert next1.status == TaskStatus.IN_PROGRESS
        await arb.complete_task(t1.task_id, result={"ok": True})
        next2 = await arb.next_task(session_id)
        assert next2.task_id == t2.task_id
        await arb.close()

    run_async(_t())


def test_request_round_trip(arb, session_id, run_async):
    async def _t():
        await arb.start()
        await arb.open_session(session_id, initial_team_id="t1")
        arb.register_request_kind("k.x", input_schema={}, response_schema={})
        arb.register_request_handler("t2", "k.x", "handler")
        req = await arb.create_request(
            session_id=session_id,
            from_team="t1",
            to_team="t2",
            kind="k.x",
            input_data={"x": 1},
        )
        fetched = await arb.get_request(req.request_id)
        assert fetched is not None
        assert fetched.from_team == "t1"
        assert fetched.to_team == "t2"
        assert fetched.kind == "k.x"
        assert fetched.input_json == {"x": 1}
        assert fetched.status == RequestStatus.PENDING
        assert fetched.response_json is None
        await arb.close()

    run_async(_t())


def test_schedule_round_trip_and_index(arb, session_id, run_async):
    async def _t():
        await arb.start()
        await arb.open_session(session_id, initial_team_id="pm")
        row = await arb.create_schedule_item(
            session_id=session_id,
            team_id="pm",
            milestone_name="m1",
            status="planned",
            target_date="2026-05-01",
        )
        assert row["schedule_id"].startswith("sched_")
        items = await arb.list_schedule_items(session_id, team_id="pm")
        assert len(items) == 1
        assert items[0]["milestone_name"] == "m1"
        assert items[0]["target_date"] == "2026-05-01"
        await arb.close()

    run_async(_t())


def test_todo_round_trip_and_index(arb, session_id, run_async):
    async def _t():
        await arb.start()
        await arb.open_session(session_id, initial_team_id="pm")
        await arb.create_todo_item(
            session_id=session_id,
            team_id="pm",
            title="do thing",
            status="open",
            owner="alice",
            milestone_name="m1",
        )
        items = await arb.list_todo_items(session_id)
        assert len(items) == 1
        assert items[0]["title"] == "do thing"
        assert items[0]["owner"] == "alice"
        # Index on (session_id, status) — exercise it.
        open_items = await arb._storage.fetch_all(  # noqa: SLF001
            "todo",
            where={"session_id": str(session_id), "status": "open"},
        )
        assert len(open_items) == 1
        await arb.close()

    run_async(_t())


def test_decision_round_trip(arb, session_id, run_async):
    async def _t():
        await arb.start()
        await arb.open_session(session_id, initial_team_id="pm")
        await arb.create_decision_item(
            session_id=session_id,
            team_id="pm",
            title="t",
            rationale="r",
            decided_by="user",
        )
        items = await arb.list_decision_items(session_id)
        assert len(items) == 1
        assert items[0]["title"] == "t"
        assert items[0]["rationale"] == "r"
        assert items[0]["decided_by"] == "user"
        await arb.close()

    run_async(_t())
