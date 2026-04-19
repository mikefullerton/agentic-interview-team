"""SpecialistDispatcher — one plan_node → one `claude -p` subprocess for the
specialist, with worker/verifier subagents invoked internally via the Task tool.

This class wraps an inner Dispatcher (real or mock) and translates its
stream of events into child `dispatch` rows. The specialist's final
structured output is expected to include an `attempts` list that groups
child dispatches into worker+verifier pairs with verdicts.
"""
from __future__ import annotations

from typing import Any

from ..arbitrator import Arbitrator
from .base import (
    AgentDefinition,
    DispatchCorrelation,
    Dispatcher,
)
from .stream_parser import SubagentStreamParser

_SUBAGENT_KIND = {
    "speciality-worker": "worker",
    "speciality-verifier": "verifier",
}


class SpecialistDispatcher:
    def __init__(self, inner: Dispatcher, arbitrator: Arbitrator):
        self._inner = inner
        self._arb = arbitrator

    async def run_specialist(
        self,
        *,
        session_id,
        team_id: str,
        plan_node_id: str | None,
        specialist_name: str,
        specialist_prompt: str,
        worker_focus: str,
        verify_criteria: str,
        logical_model: str,
        subagent_defs: list[AgentDefinition],
        timeout_seconds: float = 300.0,
    ) -> dict[str, Any]:
        parent = await self._arb.create_dispatch(
            session_id=session_id, team_id=team_id,
            plan_node_id=plan_node_id,
            agent_kind="specialist", agent_name=specialist_name,
            logical_model=logical_model,
        )
        parent_id = parent["dispatch_id"]

        parser = SubagentStreamParser()
        tool_use_to_dispatch: dict[str, str] = {}

        async def sink(event: dict) -> None:
            step = parser.ingest(event)
            for start in step.starts:
                kind = _SUBAGENT_KIND.get(start.subagent_name, "worker")
                child = await self._arb.create_dispatch(
                    session_id=session_id, team_id=team_id,
                    plan_node_id=plan_node_id,
                    parent_dispatch_id=parent_id,
                    agent_kind=kind,
                    agent_name=start.subagent_name,
                    logical_model=logical_model,
                )
                tool_use_to_dispatch[start.tool_use_id] = child["dispatch_id"]
            for end in step.ends:
                d_id = tool_use_to_dispatch.get(end.tool_use_id)
                if d_id is not None:
                    await self._arb.close_dispatch(d_id, status="completed")

        agent = AgentDefinition(
            name=specialist_name, prompt=specialist_prompt,
            logical_model=logical_model,
        )
        correlation = DispatchCorrelation(
            session_id=session_id, team_id=team_id,
            agent_id=specialist_name,
            dispatch_id=parent_id,
        )

        task_prompt = (
            f"Worker focus:\n{worker_focus}\n\n"
            f"Verify criteria:\n{verify_criteria}\n\n"
            "Invoke the speciality-worker subagent first. Pass it the "
            "worker focus and any relevant context. Then invoke the "
            "speciality-verifier subagent with the worker's output "
            "and the verify criteria. Return a single JSON object:\n"
            '{"result": <worker output>, "attempts": [{"worker_tool_use_id": '
            '"<id>", "verifier_tool_use_id": "<id or null>", '
            '"verdict": "pass"|"fail"}]}'
        )

        result = await self._inner.dispatch(
            agent=agent,
            prompt=task_prompt,
            logical_model=logical_model,
            response_schema=None,
            correlation=correlation,
            event_sink=sink,
            timeout_seconds=timeout_seconds,
        )

        await self._arb.close_dispatch(parent_id, status="completed")

        response = result.response if isinstance(result.response, dict) else {}
        attempts_dec = response.get("attempts", []) if isinstance(response, dict) else []
        created_result = await self._arb.create_result(
            session_id=session_id, team_id=team_id,
            specialist_id=specialist_name, passed=True,
            summary={"result": response.get("result")},
            plan_node_id=plan_node_id,
        )
        for n, a in enumerate(attempts_dec, 1):
            w_tu = a.get("worker_tool_use_id")
            v_tu = a.get("verifier_tool_use_id")
            w_dispatch = tool_use_to_dispatch.get(w_tu)
            if w_dispatch is None:
                continue
            v_dispatch = tool_use_to_dispatch.get(v_tu) if v_tu else None
            await self._arb.create_attempt(
                result_id=created_result.result_id,
                session_id=session_id,
                attempt_kind="speciality",
                attempt_number=n,
                worker_dispatch_id=w_dispatch,
                verifier_dispatch_id=v_dispatch,
                verdict=a.get("verdict"),
            )

        return {"response": result.response, "dispatch_id": parent_id}
