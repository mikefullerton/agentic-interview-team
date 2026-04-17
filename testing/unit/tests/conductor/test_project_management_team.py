"""Standalone project-management team — spec §6.1, step 4.

A caller team sends three PM requests (schedule, todo, decision) to the
new project-management team. Verify rows land in the correct tables
and the response payloads flow back into the caller's specialty context.
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
from services.conductor.playbook.types import (  # noqa: E402
    Manifest,
    SendRequest,
    State,
    TeamPlaybook,
    Transition,
)
from services.conductor.team_lead import TeamLead  # noqa: E402


PLAYBOOKS_DIR = (
    REPO_ROOT / "plugins" / "dev-team" / "services" / "conductor" / "playbooks"
)


def _caller_playbook() -> TeamPlaybook:
    return TeamPlaybook(
        name="pm-caller",
        states=[
            State(
                name="create_schedule",
                entry_actions=(
                    SendRequest(
                        kind="pm.schedule.create",
                        to_team="project-management",
                        input_data={
                            "milestone_name": "walking-skeleton",
                            "status": "planned",
                            "target_date": "2026-04-18",
                        },
                        response_context_key="schedule_row",
                    ),
                ),
            ),
            State(
                name="create_todo",
                entry_actions=(
                    SendRequest(
                        kind="pm.todo.create",
                        to_team="project-management",
                        input_data={
                            "title": "wire PM team",
                            "status": "open",
                            "owner": "conductor",
                            "milestone_name": "walking-skeleton",
                        },
                        response_context_key="todo_row",
                    ),
                ),
            ),
            State(
                name="create_decision",
                entry_actions=(
                    SendRequest(
                        kind="pm.decision.create",
                        to_team="project-management",
                        input_data={
                            "title": "use standalone PM team",
                            "rationale": "avoid refactor of dev-team in step 4",
                            "decided_by": "user",
                        },
                        response_context_key="decision_row",
                    ),
                ),
            ),
            State(name="done", terminal=True),
        ],
        transitions=[
            Transition("create_schedule", "create_todo"),
            Transition("create_todo", "create_decision"),
            Transition("create_decision", "done"),
        ],
        judgment_specs={},
        manifest=Manifest(),
        initial_state="create_schedule",
    )


def test_pm_team_round_trip(tmp_path):
    async def _t():
        caller = _caller_playbook()
        pm = load_playbook(PLAYBOOKS_DIR / "project_management.py")

        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arbitrator = Arbitrator(backend)
        await arbitrator.start()

        dispatcher = MockDispatcher()

        conductor = Conductor(
            arbitrator=arbitrator,
            dispatcher=dispatcher,
            team_lead=TeamLead(caller),
            session_id=uuid4(),
            aux_team_leads=[TeamLead(pm)],
        )

        await conductor.run()
        sid = conductor._session_id  # noqa: SLF001 — test introspection

        # Session completed successfully.
        row = await backend.fetch_one("session", {"session_id": str(sid)})
        assert row is not None
        assert row["status"] == SessionStatus.COMPLETED.value

        # Three requests, all completed, keyed to project-management team.
        request_rows = await backend.fetch_all(
            "request", where={"session_id": str(sid)}
        )
        assert len(request_rows) == 3
        assert all(
            r["status"] == RequestStatus.COMPLETED.value for r in request_rows
        )
        assert all(r["to_team"] == "project-management" for r in request_rows)

        # Resource rows landed in the correct tables, tagged with the
        # project-management team_id.
        schedule_rows = await backend.fetch_all(
            "schedule", where={"session_id": str(sid)}
        )
        assert len(schedule_rows) == 1
        assert schedule_rows[0]["milestone_name"] == "walking-skeleton"
        assert schedule_rows[0]["status"] == "planned"
        assert schedule_rows[0]["target_date"] == "2026-04-18"
        assert schedule_rows[0]["team_id"] == "project-management"

        todo_rows = await backend.fetch_all(
            "todo", where={"session_id": str(sid)}
        )
        assert len(todo_rows) == 1
        assert todo_rows[0]["title"] == "wire PM team"
        assert todo_rows[0]["owner"] == "conductor"
        assert todo_rows[0]["milestone_name"] == "walking-skeleton"
        assert todo_rows[0]["team_id"] == "project-management"

        decision_rows = await backend.fetch_all(
            "decision", where={"session_id": str(sid)}
        )
        assert len(decision_rows) == 1
        assert decision_rows[0]["title"] == "use standalone PM team"
        assert "refactor" in decision_rows[0]["rationale"]
        assert decision_rows[0]["decided_by"] == "user"
        assert decision_rows[0]["team_id"] == "project-management"

        # Three handler state nodes — one per PM kind — all popped.
        state_rows = await backend.fetch_all(
            "state", where={"session_id": str(sid)}
        )
        handler_nodes = [
            s for s in state_rows if s["state_name"].startswith("handler:")
        ]
        assert len(handler_nodes) == 3
        assert all(s["team_id"] == "project-management" for s in handler_nodes)
        assert all(s["exit_date"] is not None for s in handler_nodes)

        await arbitrator.close()

    asyncio.run(_t())
