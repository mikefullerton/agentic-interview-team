"""plan_realizer — one dispatch per speciality, writes plan_nodes + edges.

Given a team manifest and a goal string, make_plan_realizer returns an
async callable that:

1. Dispatches once per (specialist, speciality) via the supplied
   Dispatcher, each keyed on agent name `<specialist>-<speciality>-planner`.
2. Parses each response's `plan_nodes` list and creates a plan_node row
   per entry, scoped to the supplied roadmap_id.
3. Parses each response's `depends_on` list of `{from, to}` title pairs
   and writes a node_dependency edge per entry.

Titles are globally unique across the roadmap — the planner is
expected to namespace its titles so cross-speciality edges can resolve
by title.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))

from services.conductor.arbitrator import Arbitrator  # noqa: E402
from services.conductor.arbitrator.backends import SqliteBackend  # noqa: E402
from services.conductor.arbitrator.models import NodeKind  # noqa: E402
from services.conductor.dispatcher import MockDispatcher  # noqa: E402
from services.conductor.plan_realizer import make_plan_realizer  # noqa: E402
from services.conductor.team_loader import load_team  # noqa: E402


FIXTURE = REPO_ROOT / "testing" / "fixtures" / "teams" / "plan_fixture"


def test_plan_realizer_writes_nodes_and_edges(tmp_path):
    async def _t():
        manifest = load_team(FIXTURE)
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arb = Arbitrator(backend)
        await arb.start()
        try:
            roadmap = await arb.create_roadmap("plan-test")
            session_id = uuid4()
            await arb.open_session(
                session_id,
                initial_team_id=manifest.name,
                roadmap_id=roadmap.roadmap_id,
            )

            dispatcher = MockDispatcher(
                {
                    "architect-design-planner": {
                        "plan_nodes": [
                            {
                                "title": "design-A",
                                "node_kind": "primitive",
                                "specialist": "architect",
                                "speciality": "design",
                            },
                            {
                                "title": "design-B",
                                "node_kind": "primitive",
                                "specialist": "architect",
                                "speciality": "design",
                            },
                        ],
                        "depends_on": [{"from": "design-B", "to": "design-A"}],
                    },
                    "writer-draft-planner": {
                        "plan_nodes": [
                            {
                                "title": "draft-docs",
                                "node_kind": "primitive",
                                "specialist": "writer",
                                "speciality": "draft",
                            }
                        ],
                        "depends_on": [
                            {"from": "draft-docs", "to": "design-B"}
                        ],
                    },
                }
            )

            realize = make_plan_realizer(manifest, goal="build X")
            await realize(arb, dispatcher, session_id, roadmap.roadmap_id)

            nodes = await arb.list_plan_nodes(roadmap.roadmap_id)
            titles = {n.title: n for n in nodes}
            assert set(titles) == {"design-A", "design-B", "draft-docs"}
            for title in ("design-A", "design-B", "draft-docs"):
                assert titles[title].node_kind == NodeKind.PRIMITIVE

            # design-B depends on design-A; draft-docs depends on design-B.
            deps_b = await arb.list_dependencies_of(titles["design-B"].node_id)
            assert {d.depends_on_id for d in deps_b} == {
                titles["design-A"].node_id
            }
            deps_docs = await arb.list_dependencies_of(
                titles["draft-docs"].node_id
            )
            assert {d.depends_on_id for d in deps_docs} == {
                titles["design-B"].node_id
            }
        finally:
            await arb.close()

    asyncio.run(_t())
