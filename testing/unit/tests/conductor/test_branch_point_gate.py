"""Branch-point e2e: verifier fails, conductor opens a gate, an external
helper resolves it, conductor resumes.

Exercises the chain: worker → verifier(fail) → specialty opens gate +
returns await-gate → conductor blocks → helper resolves → conductor
receives a new decision next loop iteration.
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


def test_verifier_fail_opens_gate_then_resumes(tmp_path):
    async def _t():
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arb = Arbitrator(backend)
        await arb.start()
        roadmap = await arb.create_roadmap("bp")
        # 3-node fan: root → {a, b}. With root done, a and b are
        # simultaneously runnable, forcing the LLM path.
        for nid in ("root", "a", "b"):
            await arb.create_plan_node(
                roadmap_id=roadmap.roadmap_id,
                title=nid,
                node_kind=NodeKind.PRIMITIVE,
                node_id=nid,
            )
        await arb.add_dependency("a", "root")
        await arb.add_dependency("b", "root")

        session_id = uuid4()
        await arb.open_session(
            session_id,
            initial_team_id="conductor",
            roadmap_id=roadmap.roadmap_id,
        )
        await arb.record_node_state_event(
            node_id="root",
            event_type=NodeStateEventType.DONE,
            actor="test-setup",
            session_id=session_id,
        )

        # Verifier fails once; after the gate is resolved, subsequent
        # scheduler calls don't need the verifier (the remaining work
        # becomes deterministic as nodes run to completion).
        verifier_calls = {"n": 0}

        def verifier_resp(_prompt):
            verifier_calls["n"] += 1
            if verifier_calls["n"] == 1:
                return {"verdict": "fail", "reason": "not sure"}
            return {"verdict": "pass", "reason": "ok"}

        dispatcher = MockDispatcher(
            {
                "whats-next-worker": {
                    "action": "advance-to",
                    "node_id": "b",
                    "reason": "pick b",
                    "deterministic": False,
                },
                "whats-next-verifier": verifier_resp,
            }
        )
        conductor = Conductor(
            arbitrator=arb,
            dispatcher=dispatcher,
            team_lead=None,
            session_id=session_id,
        )

        async def resolver():
            # Wait for the gate to be created, then accept.
            while True:
                gates = await arb.list_gates(session_id, only_open=True)
                if gates:
                    await arb.resolve_gate(
                        gates[0]["gate_id"], verdict="accept-worker"
                    )
                    return
                await asyncio.sleep(0.02)

        await asyncio.gather(
            conductor.run_roadmap(
                [WhatsNextSpecialty()], await_poll_seconds=0.02
            ),
            resolver(),
        )

        session_row = await arb._storage.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        assert session_row["status"] == SessionStatus.COMPLETED.value
        for nid in ("root", "a", "b"):
            latest = await arb.latest_node_state(nid)
            assert latest is not None and latest.event_type.value == "done"

        assert verifier_calls["n"] >= 1
        gates = await arb.list_gates(session_id)
        conflict_gates = [g for g in gates if g["category"] == "conflict"]
        assert len(conflict_gates) == 1
        assert conflict_gates[0]["verdict"] == "accept-worker"
        await arb.close()

    asyncio.run(_t())
