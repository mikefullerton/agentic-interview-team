"""Team loader + generic realizer end-to-end.

Loads the real `teams/devteam/` markdown team and verifies:
1. Specialists and specialties are discovered with non-empty prompts.
2. A small hand-built roadmap referencing two of devteam's real
   specialty slugs runs to completion under the generic realizer +
   MockDispatcher (no LLM cost).
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))

from services.conductor.arbitrator import Arbitrator, SessionStatus  # noqa: E402
from services.conductor.arbitrator.backends import SqliteBackend  # noqa: E402
from services.conductor.arbitrator.models import NodeKind  # noqa: E402
from services.conductor.conductor import Conductor  # noqa: E402
from services.conductor.dispatcher import MockDispatcher  # noqa: E402
from services.conductor.generic_realizer import make_generic_realizer  # noqa: E402
from services.conductor.specialty import WhatsNextSpecialty  # noqa: E402
from services.conductor.team_loader import load_team  # noqa: E402


TEAMS_ROOT = REPO_ROOT / "teams"


def test_load_devteam_finds_specialists_and_specialties():
    manifest = load_team(TEAMS_ROOT / "devteam")
    assert manifest.name
    # Real devteam ships with many specialists; just assert the loader
    # found some with at least one parseable specialty each.
    assert len(manifest.specialists) > 0
    for specialist in manifest.specialists.values():
        assert specialist.specialties, (
            f"specialist {specialist.name!r} has no specialties"
        )
        for specialty in specialist.specialties.values():
            assert specialty.worker_focus, (
                f"{specialist.name}.{specialty.name} missing worker_focus"
            )


def test_generic_realizer_runs_small_devteam_roadmap(tmp_path):
    """Load devteam, pick two real specialty slugs, build a 2-node
    roadmap referencing them, and run the conductor under a mock
    dispatcher. Assert both nodes reach done and result rows carry the
    mocked output."""

    async def _t():
        manifest = load_team(TEAMS_ROOT / "devteam")
        # Pick any specialist that has at least one specialty.
        picked_specialist = next(
            s for s in manifest.specialists.values() if s.specialties
        )
        picked_specialty_names = list(picked_specialist.specialties.keys())
        assert picked_specialty_names, "devteam has no specialties"
        # Build a 2-node roadmap: first specialty → one more specialty
        # (or the same specialty twice if only one exists).
        specialty_a = picked_specialty_names[0]
        specialty_b = (
            picked_specialty_names[1]
            if len(picked_specialty_names) > 1
            else picked_specialty_names[0]
        )

        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arb = Arbitrator(backend)
        await arb.start()
        roadmap = await arb.create_roadmap("devteam-mini")
        await arb.create_plan_node(
            roadmap_id=roadmap.roadmap_id,
            title="node-a",
            node_kind=NodeKind.PRIMITIVE,
            node_id="node-a",
            specialist=picked_specialist.name,
            speciality=specialty_a,
        )
        await arb.create_plan_node(
            roadmap_id=roadmap.roadmap_id,
            title="node-b",
            node_kind=NodeKind.PRIMITIVE,
            node_id="node-b",
            specialist=picked_specialist.name,
            speciality=specialty_b,
        )
        await arb.add_dependency("node-b", "node-a")

        session_id = uuid4()
        await arb.open_session(
            session_id,
            initial_team_id=manifest.name,
            roadmap_id=roadmap.roadmap_id,
        )

        # Specialist path: one dispatcher call per plan_node keyed by
        # specialist name. The return envelope carries the worker output
        # plus an (empty) attempts array. MockDispatcher does not emit
        # Task tool_use events, so no child dispatches are recorded —
        # the realizer still writes a result row from the envelope.
        focus_a = picked_specialist.specialties[specialty_a].worker_focus
        focus_b = picked_specialist.specialties[specialty_b].worker_focus

        def _response_for(prompt: str):
            if specialty_a == specialty_b or focus_a in prompt:
                return {"result": {"note": "a-output"}, "attempts": []}
            return {"result": {"note": "b-output"}, "attempts": []}

        dispatcher = MockDispatcher(
            {picked_specialist.name: _response_for}
        )

        conductor = Conductor(
            arbitrator=arb,
            dispatcher=dispatcher,
            team_lead=None,
            session_id=session_id,
        )
        await conductor.run_roadmap(
            [WhatsNextSpecialty()],
            realize_primitive=make_generic_realizer(manifest),
        )

        session_row = await arb._storage.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        assert session_row["status"] == SessionStatus.COMPLETED.value
        for nid in ("node-a", "node-b"):
            latest = await arb.latest_node_state(nid)
            assert latest is not None and latest.event_type.value == "done"

        # Results carry the mocked output.
        results = await arb.list_results(session_id, team_id=manifest.name)
        by_node = {r.plan_node_id: r for r in results}
        assert by_node["node-a"].summary_json["result"] == {"note": "a-output"}
        assert "result" in by_node["node-b"].summary_json
        await arb.close()

    asyncio.run(_t())
