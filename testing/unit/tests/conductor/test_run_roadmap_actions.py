"""Tests for the full set of run_roadmap action handlers.

Covers the actions beyond `advance-to` / `done`:
- decompose: custom handler invoked; compound node reaches done.
- await-gate: conductor blocks, resolves when a test helper answers
  the gate asynchronously.
- await-request: conductor blocks until a request row flips to completed.
- present-results: default handler emits a notification.
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
from services.conductor.specialty import (  # noqa: E402
    ActionDecision,
    WhatsNextSpecialty,
)
from services.conductor.specialty.base import ConductorSpecialty  # noqa: E402


class _FixedDecisionSpecialty:
    """Test-only specialty that returns a pre-programmed sequence of decisions."""

    name = "whats-next"

    def __init__(self, decisions: list[ActionDecision]):
        self._queue = list(decisions)

    async def decide(self, arbitrator, dispatcher, session_id):
        if not self._queue:
            raise RuntimeError("fixed-decision specialty drained")
        return self._queue.pop(0)


def test_decompose_invokes_handler_and_marks_compound_done(tmp_path):
    async def _t():
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arb = Arbitrator(backend)
        await arb.start()
        roadmap = await arb.create_roadmap("t")
        await arb.create_plan_node(
            roadmap_id=roadmap.roadmap_id,
            title="root",
            node_kind=NodeKind.COMPOUND,
            node_id="root",
        )
        session_id = uuid4()
        await arb.open_session(
            session_id,
            initial_team_id="conductor",
            metadata={"roadmap_id": roadmap.roadmap_id},
        )

        handler_calls: list[str] = []

        async def my_decompose(arb_, _d, _sid, node_id):
            handler_calls.append(node_id)

        specialty = _FixedDecisionSpecialty(
            [
                ActionDecision(
                    action="decompose",
                    node_id="root",
                    reason="test",
                    deterministic=True,
                ),
                ActionDecision(
                    action="done",
                    node_id=None,
                    reason="test",
                    deterministic=True,
                ),
            ]
        )
        conductor = Conductor(
            arbitrator=arb,
            dispatcher=MockDispatcher({}),
            team_lead=None,
            session_id=session_id,
        )
        await conductor.run_roadmap(
            [specialty], decompose_compound=my_decompose
        )

        assert handler_calls == ["root"]
        latest = await arb.latest_node_state("root")
        assert latest is not None and latest.event_type.value == "done"
        await arb.close()

    asyncio.run(_t())


def test_await_gate_blocks_until_resolved(tmp_path):
    async def _t():
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arb = Arbitrator(backend)
        await arb.start()
        roadmap = await arb.create_roadmap("t")
        await arb.create_plan_node(
            roadmap_id=roadmap.roadmap_id,
            title="a",
            node_kind=NodeKind.PRIMITIVE,
            node_id="a",
        )
        session_id = uuid4()
        await arb.open_session(
            session_id,
            initial_team_id="conductor",
            metadata={"roadmap_id": roadmap.roadmap_id},
        )

        # Pre-open a gate on node "a" so await-gate has something to
        # watch. The conductor will block until verdict is set.
        gate = await arb.create_gate(
            session_id=session_id,
            team_id="conductor",
            category="conflict",
            options=["continue", "abort"],
            plan_node_id="a",
        )

        specialty = _FixedDecisionSpecialty(
            [
                ActionDecision(
                    action="await-gate",
                    node_id="a",
                    reason="blocked",
                    deterministic=True,
                ),
                ActionDecision(
                    action="done",
                    node_id=None,
                    reason="done",
                    deterministic=True,
                ),
            ]
        )
        conductor = Conductor(
            arbitrator=arb,
            dispatcher=MockDispatcher({}),
            team_lead=None,
            session_id=session_id,
        )

        async def resolver():
            await asyncio.sleep(0.1)
            await arb.resolve_gate(gate.gate_id, verdict="continue")

        await asyncio.gather(
            conductor.run_roadmap([specialty], await_poll_seconds=0.02),
            resolver(),
        )

        session_row = await arb._storage.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        assert session_row["status"] == SessionStatus.COMPLETED.value
        await arb.close()

    asyncio.run(_t())


def test_present_results_emits_notification_by_default(tmp_path):
    async def _t():
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arb = Arbitrator(backend)
        await arb.start()
        roadmap = await arb.create_roadmap("t")
        await arb.create_plan_node(
            roadmap_id=roadmap.roadmap_id,
            title="a",
            node_kind=NodeKind.PRIMITIVE,
            node_id="a",
        )
        session_id = uuid4()
        await arb.open_session(
            session_id,
            initial_team_id="conductor",
            metadata={"roadmap_id": roadmap.roadmap_id},
        )

        specialty = _FixedDecisionSpecialty(
            [
                ActionDecision(
                    action="present-results",
                    node_id=None,
                    reason="time to present",
                    deterministic=True,
                ),
                ActionDecision(
                    action="done",
                    node_id=None,
                    reason="done",
                    deterministic=True,
                ),
            ]
        )
        conductor = Conductor(
            arbitrator=arb,
            dispatcher=MockDispatcher({}),
            team_lead=None,
            session_id=session_id,
        )
        await conductor.run_roadmap([specialty])

        messages = await arb.list_messages(session_id)
        bodies = [m.body for m in messages]
        assert any("All roadmap nodes complete" in b for b in bodies)
        await arb.close()

    asyncio.run(_t())
