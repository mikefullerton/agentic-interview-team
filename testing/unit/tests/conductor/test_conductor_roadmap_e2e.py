"""End-to-end: `Conductor.run_roadmap` with `WhatsNextSpecialty`.

Three scenarios:
- Linear 3-node roadmap walked via the deterministic short-circuit only
  (no LLM calls needed).
- Diamond roadmap where two nodes become simultaneously runnable,
  forcing the LLM decide path (worker + verifier).
- Smoke: a single broad test that runs a linear roadmap and asserts
  end-to-end side-effects (session completed, state events, emitted
  decision events).
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
from services.conductor.specialty import WhatsNextSpecialty  # noqa: E402


async def _build_arb_and_roadmap(tmp_path, layout):
    """layout is a list of (node_id, title, kind) and a list of (node, depends_on) deps.

    Actually we accept it as a dict: {"nodes": [...], "deps": [...]}.
    """
    backend = SqliteBackend(tmp_path / "arb.sqlite")
    arb = Arbitrator(backend)
    await arb.start()
    roadmap = await arb.create_roadmap("e2e")
    for node_id, title in layout["nodes"]:
        await arb.create_plan_node(
            roadmap_id=roadmap.roadmap_id,
            title=title,
            node_kind=NodeKind.PRIMITIVE,
            node_id=node_id,
        )
    for node, dep in layout["deps"]:
        await arb.add_dependency(node, dep)
    return arb, roadmap


def test_linear_three_node_roadmap_walks_deterministically(tmp_path):
    """A → B → C. Pure deterministic walk; no LLM invoked."""

    async def _t():
        arb, roadmap = await _build_arb_and_roadmap(
            tmp_path,
            {
                "nodes": [("a", "a"), ("b", "b"), ("c", "c")],
                "deps": [("b", "a"), ("c", "b")],
            },
        )
        session_id = uuid4()
        # Empty dispatcher — any LLM call would raise DispatchError.
        dispatcher = MockDispatcher({})
        conductor = Conductor(
            arbitrator=arb,
            dispatcher=dispatcher,
            team_lead=None,
            session_id=session_id,
        )
        # Pre-create the session row with roadmap_id in metadata so
        # whats-next can find the roadmap. (Conductor.run_roadmap
        # open_session is idempotent when the row already exists.)
        await arb.open_session(
            session_id,
            initial_team_id="conductor",
            metadata={"roadmap_id": roadmap.roadmap_id},
        )

        await conductor.run_roadmap([WhatsNextSpecialty()])

        session_row = await arb._storage.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        assert session_row["status"] == SessionStatus.COMPLETED.value

        events = await arb.list_events(session_id)
        decisions = [
            e for e in events if e.kind == "whats_next_decision"
        ]
        actions = [e.payload_json["action"] for e in decisions]
        assert actions == ["advance-to", "advance-to", "advance-to", "done"]
        assert all(
            d.payload_json["deterministic"] for d in decisions
        ), "every decision should be deterministic for a linear DAG"

        # Every node ended in `done`.
        for nid in ("a", "b", "c"):
            latest = await arb.latest_node_state(nid)
            assert latest is not None
            assert latest.event_type.value == "done"

        await arb.close()

    asyncio.run(_t())


def test_diamond_roadmap_uses_llm_for_branch_point(tmp_path):
    """A → {B, C} → D. After A done, both B and C runnable; LLM picks."""

    async def _t():
        arb, roadmap = await _build_arb_and_roadmap(
            tmp_path,
            {
                "nodes": [("a", "a"), ("b", "b"), ("c", "c"), ("d", "d")],
                "deps": [("b", "a"), ("c", "a"), ("d", "b"), ("d", "c")],
            },
        )
        session_id = uuid4()

        # Only one LLM call is needed: the branch point after A is done,
        # where both B and C are simultaneously runnable. Once B (or C)
        # is done, the other becomes the single runnable node and the
        # deterministic short-circuit handles the rest of the walk.
        worker_calls: list[str] = []

        def worker_response(_prompt):
            worker_calls.append("worker")
            return {
                "action": "advance-to",
                "node_id": "b",
                "reason": "pick b first",
                "deterministic": False,
            }

        verifier_calls: list[str] = []

        def verifier_response(_prompt):
            verifier_calls.append("verifier")
            return {"verdict": "pass", "reason": "ok"}

        dispatcher = MockDispatcher(
            {
                "whats-next-worker": worker_response,
                "whats-next-verifier": verifier_response,
            }
        )
        conductor = Conductor(
            arbitrator=arb,
            dispatcher=dispatcher,
            team_lead=None,
            session_id=session_id,
        )
        await arb.open_session(
            session_id,
            initial_team_id="conductor",
            metadata={"roadmap_id": roadmap.roadmap_id},
        )

        await conductor.run_roadmap([WhatsNextSpecialty()])

        session_row = await arb._storage.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        assert session_row["status"] == SessionStatus.COMPLETED.value

        for nid in ("a", "b", "c", "d"):
            latest = await arb.latest_node_state(nid)
            assert latest is not None and latest.event_type.value == "done"

        # A: deterministic (only runnable).
        # Branch point (B or C): LLM decided → picks B.
        # After B: C is only runnable → deterministic.
        # D: only runnable → deterministic.
        # Final: done (deterministic).
        assert len(worker_calls) == 1
        assert len(verifier_calls) == 1

        events = await arb.list_events(session_id)
        decisions = [
            e for e in events if e.kind == "whats_next_decision"
        ]
        llm_decisions = [
            d for d in decisions
            if not d.payload_json.get("deterministic")
            and d.payload_json.get("action") == "advance-to"
        ]
        assert len(llm_decisions) == 1
        await arb.close()

    asyncio.run(_t())


def test_smoke_linear_roadmap_end_to_end(tmp_path):
    """Integration smoke: set up a roadmap, run the conductor, verify
    end-to-end side-effects. Mirrors the "hello world" path of the
    new runtime."""

    async def _t():
        arb, roadmap = await _build_arb_and_roadmap(
            tmp_path,
            {
                "nodes": [("alpha", "alpha"), ("beta", "beta")],
                "deps": [("beta", "alpha")],
            },
        )
        session_id = uuid4()
        dispatcher = MockDispatcher({})

        # Use a custom realizer to verify the hook is called.
        realize_calls: list[str] = []

        async def my_realize(arbitrator, _d, _sid, node_id):
            realize_calls.append(node_id)

        conductor = Conductor(
            arbitrator=arb,
            dispatcher=dispatcher,
            team_lead=None,
            session_id=session_id,
        )
        await arb.open_session(
            session_id,
            initial_team_id="conductor",
            metadata={"roadmap_id": roadmap.roadmap_id},
        )

        await conductor.run_roadmap(
            [WhatsNextSpecialty()], realize_primitive=my_realize
        )

        # Session completed.
        session_row = await arb._storage.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        assert session_row["status"] == SessionStatus.COMPLETED.value

        # Realizer called for each primitive in DAG order.
        assert realize_calls == ["alpha", "beta"]

        # Both nodes done.
        for nid in ("alpha", "beta"):
            latest = await arb.latest_node_state(nid)
            assert latest.event_type.value == "done"

        # running+done events recorded for each primitive.
        storage = arb._storage
        for nid in ("alpha", "beta"):
            events = await storage.fetch_all(
                "node_state_event",
                where={"node_id": nid},
                order_by="event_date",
            )
            kinds = [e["event_type"] for e in events]
            assert "running" in kinds and "done" in kinds

        await arb.close()

    asyncio.run(_t())
