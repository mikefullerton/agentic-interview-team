"""SpecialistDispatcher drives a child dispatcher through one claude -p call,
opening child dispatch rows for each Task subagent invocation in the stream."""
from __future__ import annotations

import pytest

from services.conductor.arbitrator import Arbitrator
from services.conductor.arbitrator.backends import SqliteBackend
from services.conductor.dispatcher.specialist import SpecialistDispatcher
from services.conductor.dispatcher.mock import MockDispatcher


@pytest.fixture
def arb(tmp_path, run_async):
    a = Arbitrator(SqliteBackend(tmp_path / "arb.sqlite"))
    run_async(a.start())
    yield a
    run_async(a.close())


def test_specialist_dispatcher_records_parent_and_child_dispatches(
    arb, run_async, session_id,
):
    run_async(arb.open_session(session_id, initial_team_id="t"))

    inner = MockDispatcher()

    async def fake_dispatch(agent, prompt, logical_model, response_schema,
                            correlation, event_sink, timeout_seconds=300.0):
        await event_sink({
            "type": "tool_use", "id": "tu1", "name": "Task",
            "input": {"subagent_type": "speciality-worker",
                      "description": "work", "prompt": "p"},
        })
        await event_sink({
            "type": "tool_result", "tool_use_id": "tu1",
            "content": [{"type": "text", "text": '{"output": "ok"}'}],
        })
        from services.conductor.dispatcher.base import DispatchResult
        return DispatchResult(
            response={
                "result": {"output": "ok"},
                "attempts": [{
                    "worker_tool_use_id": "tu1",
                    "verdict": "pass",
                }],
            },
            duration_ms=1, events=2, terminated_normally=True,
        )
    inner.dispatch = fake_dispatch  # type: ignore[assignment]

    sd = SpecialistDispatcher(inner=inner, arbitrator=arb)
    out = run_async(sd.run_specialist(
        session_id=session_id, team_id="t",
        plan_node_id=None,
        specialist_name="platform-database",
        specialist_prompt="You are the database specialist...",
        worker_focus="Review indexes.",
        verify_criteria="Query plan uses them.",
        logical_model="balanced",
        subagent_defs=[],
    ))

    rows = run_async(arb._storage.fetch_all("dispatch"))
    kinds = sorted(r["agent_kind"] for r in rows)
    assert kinds == ["specialist", "worker"]
    parent = next(r for r in rows if r["agent_kind"] == "specialist")
    child = next(r for r in rows if r["agent_kind"] == "worker")
    assert child["parent_dispatch_id"] == parent["dispatch_id"]

    attempts = run_async(arb._storage.fetch_all("attempt"))
    assert len(attempts) == 1
    assert attempts[0]["verdict"] == "pass"
    assert attempts[0]["worker_dispatch_id"] == child["dispatch_id"]

    assert out["response"]["result"]["output"] == "ok"
