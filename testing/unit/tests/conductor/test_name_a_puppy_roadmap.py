"""End-to-end: name-a-puppy as a roadmap run under the new conductor.

Exercises the full phase-2 integration: build roadmap → open session
with roadmap_id in metadata → run_roadmap with WhatsNextSpecialty and
the puppy realizer → assert full walk order, LLM dispatch counts,
ranked output, messages, session completion.
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
from services.conductor.conductor import Conductor  # noqa: E402
from services.conductor.dispatcher import MockDispatcher  # noqa: E402
from services.conductor.playbooks.name_a_puppy_roadmap import (  # noqa: E402
    TEAM_ID,
    build_roadmap,
    realize,
)
from services.conductor.specialty import WhatsNextSpecialty  # noqa: E402


RANKED = ["Luna", "Biscuit", "Daisy", "Scout", "Rex"]


def _build_dispatcher() -> MockDispatcher:
    # Expected scheduler path:
    #   gather-traits: 1 runnable → deterministic (no LLM)
    #   3 siblings runnable → LLM picks breed-names            [LLM #1]
    #   2 siblings runnable → LLM picks lifestyle-names        [LLM #2]
    #   temperament-names: 1 runnable → deterministic
    #   aggregate: 1 runnable → deterministic
    #   present: 1 runnable → deterministic
    #   all done → deterministic
    scheduler_queue = [
        {
            "action": "advance-to",
            "node_id": "breed-names",
            "reason": "pick breed first",
            "deterministic": False,
        },
        {
            "action": "advance-to",
            "node_id": "lifestyle-names",
            "reason": "lifestyle next",
            "deterministic": False,
        },
    ]

    def scheduler_worker(_prompt):
        if not scheduler_queue:
            raise RuntimeError("scheduler worker called more times than expected")
        return scheduler_queue.pop(0)

    return MockDispatcher(
        {
            # Scheduler pair
            "whats-next-worker": scheduler_worker,
            "whats-next-verifier": {"verdict": "pass", "reason": "ok"},
            # Naming workers
            "breed-name-worker": {
                "candidates": ["Biscuit", "Sable", "Honey"]
            },
            "lifestyle-name-worker": {
                "candidates": ["Scout", "River", "Sage"]
            },
            "temperament-name-worker": {
                "candidates": ["Luna", "Daisy", "Rex"]
            },
            # Aggregator
            "aggregator-worker": {"ranked_candidates": RANKED},
        }
    )


def test_name_a_puppy_roadmap_end_to_end(tmp_path):
    async def _t():
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arb = Arbitrator(backend)
        await arb.start()

        roadmap_id = await build_roadmap(arb)

        session_id = uuid4()
        await arb.open_session(
            session_id,
            initial_team_id=TEAM_ID,
            metadata={"roadmap_id": roadmap_id},
        )

        dispatcher = _build_dispatcher()
        conductor = Conductor(
            arbitrator=arb,
            dispatcher=dispatcher,
            team_lead=None,
            session_id=session_id,
        )

        await conductor.run_roadmap(
            [WhatsNextSpecialty()],
            realize_primitive=realize,
        )

        # Session completed.
        session_row = await arb._storage.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        assert session_row["status"] == SessionStatus.COMPLETED.value

        # Every plan node ended in `done`.
        for node_id in (
            "gather-traits",
            "breed-names",
            "lifestyle-names",
            "temperament-names",
            "aggregate",
            "present",
        ):
            latest = await arb.latest_node_state(node_id)
            assert latest is not None and latest.event_type.value == "done", (
                f"{node_id} did not reach done; latest={latest}"
            )

        # Three naming specialties each wrote a result with 3 candidates;
        # aggregate wrote the ranked list; presenter wrote a count.
        results = await arb.list_results(session_id, team_id=TEAM_ID)
        by_node = {r.plan_node_id: r for r in results}
        assert len(by_node) == 6
        for nid in ("breed-names", "lifestyle-names", "temperament-names"):
            assert len(by_node[nid].summary_json["candidates"]) == 3
        assert by_node["aggregate"].summary_json["ranked_candidates"] == RANKED
        assert by_node["present"].summary_json["presented_count"] == len(RANKED)

        # Final presented message reflects the ranked list.
        messages = await arb.list_messages(session_id)
        bodies = [m.body for m in messages]
        present_body = bodies[-1]
        assert "Top candidate names:" in present_body
        for i, name in enumerate(RANKED, 1):
            assert f"{i}. {name}" in present_body

        # Scheduler LLM called exactly 2 times (branch-point decisions at
        # the two moments where multiple siblings were runnable). All
        # other steps short-circuit deterministically.
        events = await arb.list_events(session_id)
        decisions = [
            e for e in events if e.kind == "whats_next_decision"
        ]
        llm_decisions = [
            d for d in decisions if not d.payload_json.get("deterministic")
        ]
        assert len(llm_decisions) == 2, (
            f"expected 2 LLM scheduler calls, got {len(llm_decisions)}"
        )

        await arb.close()

    asyncio.run(_t())
