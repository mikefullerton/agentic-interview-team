"""Realizer now routes each plan_node through SpecialistDispatcher, so a
parent specialist dispatch + child worker/verifier dispatches appear in the
arbitrator for every realized node."""
from __future__ import annotations

import pytest

from services.conductor.arbitrator import Arbitrator
from services.conductor.arbitrator.backends import SqliteBackend
from services.conductor.arbitrator.models import NodeKind
from services.conductor.dispatcher.mock import MockDispatcher
from services.conductor.generic_realizer import make_generic_realizer
from services.conductor.team_loader import (
    SpecialistDef, SpecialtyDef, TeamManifest,
)


@pytest.fixture
def arb(tmp_path, run_async):
    a = Arbitrator(SqliteBackend(tmp_path / "arb.sqlite"))
    run_async(a.start())
    yield a
    run_async(a.close())


def test_realizer_creates_specialist_dispatch_and_children(
    arb, run_async, session_id, tmp_path,
):
    run_async(arb.open_session(session_id, initial_team_id="devteam"))
    rm = run_async(arb.create_roadmap("R"))
    node = run_async(arb.create_plan_node(
        rm.roadmap_id, "idx", NodeKind.PRIMITIVE,
        node_id="n-idx",
        specialist="platform-database",
        speciality="indexing",
    ))

    manifest = TeamManifest(name="devteam", team_root=tmp_path)
    manifest.specialists["platform-database"] = SpecialistDef(
        name="platform-database",
        specialties={
            "indexing": SpecialtyDef(
                name="indexing", description="Index review",
                worker_focus="Review indexes.",
                verify="Query plan uses them.",
            ),
        },
    )

    dispatcher = MockDispatcher()
    async def fake(agent, prompt, logical_model, response_schema,
                   correlation, event_sink, timeout_seconds=300.0):
        await event_sink({
            "type": "tool_use", "id": "tu-w", "name": "Task",
            "input": {"subagent_type": "speciality-worker",
                      "description": "work", "prompt": "p"},
        })
        await event_sink({
            "type": "tool_result", "tool_use_id": "tu-w",
            "content": [{"type": "text", "text": "{}"}],
        })
        from services.conductor.dispatcher.base import DispatchResult
        return DispatchResult(
            response={"result": {"ok": True},
                       "attempts": [{"worker_tool_use_id": "tu-w",
                                      "verdict": "pass"}]},
            duration_ms=1, events=2, terminated_normally=True,
        )
    dispatcher.dispatch = fake  # type: ignore[assignment]

    realize = make_generic_realizer(manifest)
    run_async(realize(arb, dispatcher, session_id, node.node_id))

    rows = run_async(arb._storage.fetch_all("dispatch"))
    kinds = sorted(r["agent_kind"] for r in rows)
    assert kinds == ["specialist", "worker"]

    attempts = run_async(arb._storage.fetch_all("attempt"))
    assert len(attempts) == 1
    assert attempts[0]["verdict"] == "pass"
