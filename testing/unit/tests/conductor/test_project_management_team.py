"""project-management — direct request-handler registration (no playbook).

The caller posts three requests (schedule, todo, decision) via the
arbitrator; `run_callable_handlers_once` drains the queue by invoking
the registered callable handlers. Rows land in the correct tables and
responses flow back through each request's response_json.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))

from services.conductor.arbitrator import (  # noqa: E402
    Arbitrator,
    RequestStatus,
)
from services.conductor.arbitrator.backends import SqliteBackend  # noqa: E402
from services.conductor.playbooks import project_management  # noqa: E402


def test_pm_callable_handlers_round_trip(tmp_path):
    async def _t():
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arb = Arbitrator(backend)
        await arb.start()

        session_id = uuid4()
        await arb.open_session(session_id, initial_team_id="pm-caller")

        project_management.register(arb)

        await arb.create_request(
            session_id=session_id,
            from_team="pm-caller",
            to_team=project_management.TEAM_ID,
            kind="pm.schedule.create",
            input_data={
                "milestone_name": "walking-skeleton",
                "status": "planned",
                "target_date": "2026-04-18",
            },
        )
        await arb.create_request(
            session_id=session_id,
            from_team="pm-caller",
            to_team=project_management.TEAM_ID,
            kind="pm.todo.create",
            input_data={
                "title": "wire PM team",
                "status": "open",
                "owner": "conductor",
                "milestone_name": "walking-skeleton",
            },
        )
        await arb.create_request(
            session_id=session_id,
            from_team="pm-caller",
            to_team=project_management.TEAM_ID,
            kind="pm.decision.create",
            input_data={
                "title": "use callable PM handlers",
                "rationale": "avoid playbook shell for mechanical writes",
                "decided_by": "user",
            },
        )

        drained = await arb.run_callable_handlers_once(session_id)
        assert drained == 3

        request_rows = await backend.fetch_all(
            "request", where={"session_id": str(session_id)}
        )
        assert all(
            r["status"] == RequestStatus.COMPLETED.value for r in request_rows
        )
        # Each request carries a non-null response_json referencing the
        # newly-inserted row.
        for r in request_rows:
            assert r["response_json"]
            payload = json.loads(r["response_json"])
            assert isinstance(payload, dict)

        schedule_rows = await backend.fetch_all(
            "schedule", where={"session_id": str(session_id)}
        )
        assert len(schedule_rows) == 1
        assert schedule_rows[0]["milestone_name"] == "walking-skeleton"
        assert schedule_rows[0]["team_id"] == project_management.TEAM_ID

        todo_rows = await backend.fetch_all(
            "todo", where={"session_id": str(session_id)}
        )
        assert len(todo_rows) == 1
        assert todo_rows[0]["title"] == "wire PM team"

        decision_rows = await backend.fetch_all(
            "decision", where={"session_id": str(session_id)}
        )
        assert len(decision_rows) == 1
        body = await arb.get_body("decision", decision_rows[0]["decision_id"])
        assert body is not None
        assert "playbook" in body.body_text

        await arb.close()

    asyncio.run(_t())
