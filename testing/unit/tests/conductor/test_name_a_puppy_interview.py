"""Real-interview variant of the puppy roadmap.

Uses `make_realizer(interview=True)` so `gather-traits` asks 4 questions
via `ask_user` instead of reading `DEFAULT_TRAITS`. A concurrent helper
answers each question. Asserts the traits collected match the answers,
and that the ranked list still emerges at the end.
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
    make_realizer,
)
from services.conductor.specialty import WhatsNextSpecialty  # noqa: E402
from services.conductor.user_interaction import (  # noqa: E402
    answer_pending_gates,
)


ANSWERS = {
    "breed": "golden retriever",
    "gender": "female",
    "coloring": "cream",
    "temperament": "playful",
}


def _dispatcher():
    return MockDispatcher(
        {
            "whats-next-worker": {
                "action": "advance-to",
                "node_id": "breed-names",
                "reason": "branch point",
                "deterministic": False,
            },
            "whats-next-verifier": {"verdict": "pass", "reason": "ok"},
            "breed-name-worker": {"candidates": ["Biscuit", "Sable", "Honey"]},
            "lifestyle-name-worker": {"candidates": ["Scout", "River", "Sage"]},
            "temperament-name-worker": {"candidates": ["Luna", "Daisy", "Rex"]},
            "aggregator-worker": {
                "ranked_candidates": ["Luna", "Biscuit", "Scout"]
            },
        }
    )


def test_interview_realizer_collects_user_answers(tmp_path):
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

        conductor = Conductor(
            arbitrator=arb,
            dispatcher=_dispatcher(),
            team_lead=None,
            session_id=session_id,
        )

        # Concurrent answerer polls for open question gates and resolves
        # them using the ANSWERS map (keyed by substring of question body).
        # Using the trait key as the substring works because every
        # question contains the trait word.
        answer_map = {
            "breed": ANSWERS["breed"],
            "gender": ANSWERS["gender"],
            "color": ANSWERS["coloring"],
            "temperament": ANSWERS["temperament"],
        }

        async def answerer():
            while True:
                # Stop when the session is completed.
                row = await arb._storage.fetch_one(
                    "session", {"session_id": str(session_id)}
                )
                if (
                    row
                    and row.get("status") == SessionStatus.COMPLETED.value
                ):
                    return
                await answer_pending_gates(arb, session_id, answer_map)
                await asyncio.sleep(0.03)

        await asyncio.gather(
            conductor.run_roadmap(
                [WhatsNextSpecialty()],
                realize_primitive=make_realizer(interview=True),
                await_poll_seconds=0.02,
            ),
            answerer(),
        )

        # Session completed.
        session_row = await arb._storage.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        assert session_row["status"] == SessionStatus.COMPLETED.value

        # Traits result reflects the answers.
        results = await arb.list_results(session_id, team_id=TEAM_ID)
        by_node = {r.plan_node_id: r for r in results}
        traits = by_node["gather-traits"].summary_json["traits"]
        for key, expected in ANSWERS.items():
            assert traits[key] == expected

        # Four question gates created; all resolved.
        rows = await arb._storage.fetch_all(
            "gate", where={"session_id": str(session_id)}
        )
        question_gates = [r for r in rows if r["category"] == "question"]
        assert len(question_gates) == 4
        assert all(r["verdict"] is not None for r in question_gates)
        await arb.close()

    asyncio.run(_t())
