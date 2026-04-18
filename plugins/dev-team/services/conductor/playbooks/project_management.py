"""project-management team — direct request handlers (no playbook shell).

Registers three callable handlers on the arbitrator:
  - ``pm.schedule.create``  → inserts a ``schedule`` row
  - ``pm.todo.create``      → inserts a ``todo`` row
  - ``pm.decision.create``  → inserts a ``decision`` row

No LLM dispatch, no state machine. A caller writes a request of one of
these kinds; the arbitrator invokes the matching handler and fills the
response with the inserted row.
"""
from __future__ import annotations

import json

from services.conductor.arbitrator import Arbitrator
from services.conductor.arbitrator.models import Request


TEAM_ID = "project-management"


async def handle_schedule_create(arb: Arbitrator, request: Request) -> dict:
    data = request.input_json or {}
    if isinstance(data, str):
        data = json.loads(data)
    row = await arb.create_schedule_item(
        session_id=request.session_id,
        team_id=TEAM_ID,
        **data,
    )
    return dict(row) if hasattr(row, "__iter__") and not isinstance(row, str) else row.__dict__


async def handle_todo_create(arb: Arbitrator, request: Request) -> dict:
    data = request.input_json or {}
    if isinstance(data, str):
        data = json.loads(data)
    row = await arb.create_todo_item(
        session_id=request.session_id,
        team_id=TEAM_ID,
        **data,
    )
    return dict(row) if hasattr(row, "__iter__") and not isinstance(row, str) else row.__dict__


async def handle_decision_create(arb: Arbitrator, request: Request) -> dict:
    data = request.input_json or {}
    if isinstance(data, str):
        data = json.loads(data)
    row = await arb.create_decision_item(
        session_id=request.session_id,
        team_id=TEAM_ID,
        **data,
    )
    return dict(row) if hasattr(row, "__iter__") and not isinstance(row, str) else row.__dict__


HANDLERS = {
    "pm.schedule.create": handle_schedule_create,
    "pm.todo.create": handle_todo_create,
    "pm.decision.create": handle_decision_create,
}


def register(arb: Arbitrator) -> None:
    """Register the PM request kinds + callable handlers on an arbitrator.

    Callers that want to send PM requests should invoke this once after
    `arb.start()` and before issuing any `pm.*` requests. Idempotent.
    """
    open_schema = {"type": "object"}
    for kind in HANDLERS:
        arb.register_request_kind(
            kind=kind, input_schema=open_schema, response_schema=open_schema
        )
    for kind, handler in HANDLERS.items():
        arb.register_request_callable(team_id=TEAM_ID, kind=kind, handler=handler)
