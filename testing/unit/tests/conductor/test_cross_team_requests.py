"""Cross-team flow: SendRequest + handler state + RespondToRequest.

Verifies that a caller team can send an inter-team request, the target
team's handler state runs and completes the request, and the response
flows back into the caller's specialty context. Exercises the
arbitrator's serial request queue from spec §7.4.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))

from services.conductor.arbitrator import (  # noqa: E402
    Arbitrator,
    RequestStatus,
    SessionStatus,
)
from services.conductor.arbitrator.backends import SqliteBackend  # noqa: E402
from services.conductor.conductor import Conductor  # noqa: E402
from services.conductor.dispatcher import MockDispatcher  # noqa: E402
from services.conductor.playbook import load_playbook  # noqa: E402
from services.conductor.team_lead import TeamLead  # noqa: E402


PLAYBOOKS_DIR = (
    REPO_ROOT / "plugins" / "dev-team" / "services" / "conductor" / "playbooks"
)


def test_cross_team_request_round_trip(tmp_path):
    async def _t():
        caller = load_playbook(PLAYBOOKS_DIR / "name_a_puppy_with_coach.py")
        coach = load_playbook(PLAYBOOKS_DIR / "pet_coach.py")

        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arbitrator = Arbitrator(backend)
        await arbitrator.start()

        dispatcher = MockDispatcher(
            {"themed-name-worker": {"candidates": ["Scout", "River", "Sage"]}}
        )

        conductor = Conductor(
            arbitrator=arbitrator,
            dispatcher=dispatcher,
            team_lead=TeamLead(caller),
            session_id=uuid4(),
            aux_team_leads=[TeamLead(coach)],
        )

        await conductor.run()
        sid = conductor._session_id  # noqa: SLF001 — test introspection

        # Session completed successfully.
        row = await backend.fetch_one("session", {"session_id": str(sid)})
        assert row is not None
        assert row["status"] == SessionStatus.COMPLETED.value

        # Exactly one request row, completed with the coach's response.
        request_rows = await backend.fetch_all(
            "request", where={"session_id": str(sid)}
        )
        assert len(request_rows) == 1
        r = request_rows[0]
        assert r["from_team"] == "name-a-puppy-with-coach"
        assert r["to_team"] == "pet-coach"
        assert r["kind"] == "pet_coach.suggest_theme"
        assert r["status"] == RequestStatus.COMPLETED.value
        import json

        response = json.loads(r["response_json"])
        assert response["theme"] == "outdoor-adventure"
        assert "hiking" in response["hints"]

        # The handler state pushed a node under the pet-coach team.
        state_rows = await backend.fetch_all(
            "state", where={"session_id": str(sid)}
        )
        handler_nodes = [
            s for s in state_rows if s["state_name"].startswith("handler:")
        ]
        assert len(handler_nodes) == 1
        assert handler_nodes[0]["team_id"] == "pet-coach"
        assert handler_nodes[0]["exit_date"] is not None

        # Caller's themed specialist ran afterwards.
        results = await arbitrator.list_results(sid)
        assert len(results) == 1
        assert results[0].specialist_id == "themed-breed"

        await arbitrator.close()

    asyncio.run(_t())


def test_unknown_handler_raises(tmp_path):
    """A SendRequest for a kind the target team doesn't handle raises KeyError."""
    from services.conductor.playbook.types import (
        Manifest,
        SendRequest,
        State,
        TeamPlaybook,
        Transition,
    )

    async def _t():
        caller = TeamPlaybook(
            name="caller",
            states=[
                State(
                    name="start",
                    entry_actions=(
                        SendRequest(
                            kind="unknown.kind",
                            to_team="pet-coach",
                            input_data={},
                        ),
                    ),
                ),
                State(name="done", terminal=True),
            ],
            transitions=[Transition("start", "done")],
            judgment_specs={},
            manifest=Manifest(),
            initial_state="start",
        )
        coach = load_playbook(PLAYBOOKS_DIR / "pet_coach.py")

        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arbitrator = Arbitrator(backend)
        await arbitrator.start()
        dispatcher = MockDispatcher()
        conductor = Conductor(
            arbitrator=arbitrator,
            dispatcher=dispatcher,
            team_lead=TeamLead(caller),
            session_id=uuid4(),
            aux_team_leads=[TeamLead(coach)],
        )
        try:
            await conductor.run()
        except KeyError as e:
            assert "unknown.kind" in str(e)
        else:
            raise AssertionError("Expected KeyError for unknown handler")
        await arbitrator.close()

    asyncio.run(_t())
