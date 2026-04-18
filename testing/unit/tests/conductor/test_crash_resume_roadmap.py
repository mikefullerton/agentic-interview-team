"""Crash-resume via the whats-next specialty.

Scenario: a session runs partway through a linear roadmap, then the
conductor is killed mid-dispatch. A new conductor instance is created
with the same session_id and roadmap. On the first `decide` call,
the specialty sees the partial state (some nodes `done`, one `running`,
rest not yet touched) and picks the right next step.

No active-state-row cleanup machinery is exercised here; the running
event for the interrupted node is left in place and the specialty is
expected to advance it (effectively retrying) via the LLM decide path
(since active state rows force the LLM decision branch).
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
from services.conductor.arbitrator.models import (  # noqa: E402
    NodeKind,
    NodeStateEventType,
)
from services.conductor.conductor import Conductor  # noqa: E402
from services.conductor.dispatcher import MockDispatcher  # noqa: E402
from services.conductor.specialty import WhatsNextSpecialty  # noqa: E402


async def _build(tmp_path):
    backend = SqliteBackend(tmp_path / "arb.sqlite")
    arb = Arbitrator(backend)
    await arb.start()
    roadmap = await arb.create_roadmap("crash-resume")
    for nid in ("a", "b", "c"):
        await arb.create_plan_node(
            roadmap_id=roadmap.roadmap_id,
            title=nid,
            node_kind=NodeKind.PRIMITIVE,
            node_id=nid,
        )
    await arb.add_dependency("b", "a")
    await arb.add_dependency("c", "b")
    return arb, roadmap


def test_resume_picks_up_after_interrupted_node(tmp_path):
    """A: done, B: running (interrupted), C: not started. A fresh
    conductor reads that state and resumes with an advance-to on B."""

    async def _t():
        arb, roadmap = await _build(tmp_path)
        session_id = uuid4()
        await arb.open_session(
            session_id, initial_team_id="conductor", roadmap_id=roadmap.roadmap_id
        )
        # Simulate a prior crashed run: A done, B started but not done.
        await arb.record_node_state_event(
            node_id="a",
            event_type=NodeStateEventType.DONE,
            actor="prior-session",
            session_id=session_id,
        )
        await arb.record_node_state_event(
            node_id="b",
            event_type=NodeStateEventType.RUNNING,
            actor="prior-session",
            session_id=session_id,
        )

        # Worker re-run returns advance-to b; verifier passes.
        dispatcher = MockDispatcher(
            {
                "whats-next-worker": {
                    "action": "advance-to",
                    "node_id": "b",
                    "reason": "resume b",
                    "deterministic": False,
                },
                "whats-next-verifier": {"verdict": "pass", "reason": "ok"},
            }
        )
        conductor = Conductor(
            arbitrator=arb,
            dispatcher=dispatcher,
            team_lead=None,
            session_id=session_id,
        )
        await conductor.run_roadmap([WhatsNextSpecialty()])

        session_row = await arb._storage.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        assert session_row["status"] == SessionStatus.COMPLETED.value
        for nid in ("a", "b", "c"):
            latest = await arb.latest_node_state(nid)
            assert latest is not None and latest.event_type.value == "done"
        await arb.close()

    asyncio.run(_t())


def test_resume_respects_already_done_nodes(tmp_path):
    """If ALL nodes are already done, a fresh conductor returns `done`
    on the first decide and terminates without dispatching anything."""

    async def _t():
        arb, roadmap = await _build(tmp_path)
        session_id = uuid4()
        await arb.open_session(
            session_id, initial_team_id="conductor", roadmap_id=roadmap.roadmap_id
        )
        for nid in ("a", "b", "c"):
            await arb.record_node_state_event(
                node_id=nid,
                event_type=NodeStateEventType.DONE,
                actor="prior-session",
                session_id=session_id,
            )

        # Empty dispatcher — any LLM call would raise.
        dispatcher = MockDispatcher({})
        conductor = Conductor(
            arbitrator=arb,
            dispatcher=dispatcher,
            team_lead=None,
            session_id=session_id,
        )
        await conductor.run_roadmap([WhatsNextSpecialty()])

        session_row = await arb._storage.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        assert session_row["status"] == SessionStatus.COMPLETED.value
        await arb.close()

    asyncio.run(_t())
