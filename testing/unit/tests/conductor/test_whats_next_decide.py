"""WhatsNextSpecialty.decide — worker / verifier paths via MockDispatcher.

Covers the branches that the deterministic short-circuit falls through
on:
- multiple runnable nodes → worker returns advance-to one of them,
  verifier passes → decision returned
- verifier says retry-with an alternative → alternative returned
- verifier says fail → worker's decision surfaced anyway (phase 1)
- worker's own `deterministic: true` skips the verifier entirely
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
from services.conductor.specialty import WhatsNextSpecialty  # noqa: E402


async def _setup_diamond_arbitrator(tmp_path):
    """Build a diamond roadmap: A → {B, C} → D. Mark A done so both B
    and C are runnable (forces the non-deterministic path)."""
    backend = SqliteBackend(tmp_path / "arb.sqlite")
    arb = Arbitrator(backend)
    await arb.start()
    roadmap = await arb.create_roadmap("diamond")
    for node_id, title in [
        ("a", "a"),
        ("b", "b"),
        ("c", "c"),
        ("d", "d"),
    ]:
        await arb.create_plan_node(
            roadmap_id=roadmap.roadmap_id,
            title=title,
            node_kind=NodeKind.PRIMITIVE,
            parent_id=None,
            node_id=node_id,
        )
    await arb.add_dependency("b", "a")
    await arb.add_dependency("c", "a")
    await arb.add_dependency("d", "b")
    await arb.add_dependency("d", "c")

    session_id = uuid4()
    await arb.open_session(
        session_id,
        initial_team_id="conductor",
        metadata={"roadmap_id": roadmap.roadmap_id},
    )

    from services.conductor.arbitrator.models import NodeStateEventType

    await arb.record_node_state_event(
        node_id="a",
        event_type=NodeStateEventType.DONE,
        actor="test-setup",
        session_id=session_id,
    )
    return arb, session_id


def test_worker_advance_to_verifier_pass(tmp_path):
    async def _t():
        arb, session_id = await _setup_diamond_arbitrator(tmp_path)

        dispatcher = MockDispatcher(
            {
                "whats-next-worker": {
                    "action": "advance-to",
                    "node_id": "b",
                    "reason": "pick b first",
                    "deterministic": False,
                },
                "whats-next-verifier": {
                    "verdict": "pass",
                    "reason": "b is runnable",
                },
            }
        )
        specialty = WhatsNextSpecialty()
        decision = await specialty.decide(arb, dispatcher, session_id)

        assert decision.action == "advance-to"
        assert decision.node_id == "b"
        assert decision.deterministic is False
        await arb.close()

    asyncio.run(_t())


def test_verifier_retry_with_alternative_overrides(tmp_path):
    async def _t():
        arb, session_id = await _setup_diamond_arbitrator(tmp_path)

        dispatcher = MockDispatcher(
            {
                "whats-next-worker": {
                    "action": "advance-to",
                    "node_id": "b",
                    "reason": "pick b",
                    "deterministic": False,
                },
                "whats-next-verifier": {
                    "verdict": "retry-with",
                    "alternative": {
                        "action": "advance-to",
                        "node_id": "c",
                        "reason": "c is higher-priority",
                        "deterministic": False,
                    },
                    "reason": "c should go first",
                },
            }
        )
        specialty = WhatsNextSpecialty()
        decision = await specialty.decide(arb, dispatcher, session_id)

        assert decision.action == "advance-to"
        assert decision.node_id == "c"
        await arb.close()

    asyncio.run(_t())


def test_worker_self_reports_deterministic_skips_verifier(tmp_path):
    async def _t():
        arb, session_id = await _setup_diamond_arbitrator(tmp_path)

        # Only the worker has a canned response. If the verifier were
        # called, MockDispatcher would raise DispatchError.
        dispatcher = MockDispatcher(
            {
                "whats-next-worker": {
                    "action": "advance-to",
                    "node_id": "b",
                    "reason": "obvious",
                    "deterministic": True,
                },
            }
        )
        specialty = WhatsNextSpecialty()
        decision = await specialty.decide(arb, dispatcher, session_id)

        assert decision.action == "advance-to"
        assert decision.node_id == "b"
        assert decision.deterministic is True
        await arb.close()

    asyncio.run(_t())


def test_verifier_fail_still_surfaces_worker_decision(tmp_path):
    """Phase 1: we don't open a gate on verifier fail yet — the worker's
    decision is returned so the conductor can at least log it. Future work
    will upgrade this to open a real gate."""

    async def _t():
        arb, session_id = await _setup_diamond_arbitrator(tmp_path)

        dispatcher = MockDispatcher(
            {
                "whats-next-worker": {
                    "action": "advance-to",
                    "node_id": "b",
                    "reason": "pick b",
                    "deterministic": False,
                },
                "whats-next-verifier": {
                    "verdict": "fail",
                    "reason": "something is wrong but we can't articulate it",
                },
            }
        )
        specialty = WhatsNextSpecialty()
        decision = await specialty.decide(arb, dispatcher, session_id)

        assert decision.action == "advance-to"
        assert decision.node_id == "b"
        await arb.close()

    asyncio.run(_t())
