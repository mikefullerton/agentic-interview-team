"""Conductor main loop — spec §5.1.

One conductor instance per session. Drives a TeamLead through its state
machine, executing each state's entry actions via the arbitrator and
dispatcher. The state tree is persisted on every push/pop so a restart
with the same session_id resumes from the last completed state.

Full main-loop features from §5.1 landed in step 2:
- Parallel DispatchSpecialist actions run concurrently (asyncio.gather)
- Judgment-driven transitions (JudgmentCall → next_state override)
- Gate creation actions
- Aggregation action ranks results via a judgment call
"""
from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from .arbitrator import Arbitrator, SessionStatus
from .dispatcher import (
    AgentDefinition,
    DispatchCorrelation,
    DispatchError,
    Dispatcher,
)
from .playbook.types import (
    Action,
    DispatchSpecialist,
    EmitMessage,
    JudgmentCall,
    PresentResults,
    WaitForUserInput,
)
from .specialist_runner import run_specialist
from .team_lead import TeamLead


@dataclass
class ConductorContext:
    """Ephemeral runtime context passed into action executors."""

    session_id: UUID
    team_id: str
    parent_state_node_id: str | None = None
    user_inputs: list[str] = field(default_factory=list)
    specialty_context: dict[str, Any] = field(default_factory=dict)
    # Judgment responses fill this; the main loop reads and clears it.
    pending_next_state: str | None = None
    # Auto-resolve gates with this verdict in the walking skeleton.
    auto_gate_verdict: str = "accept"


class Conductor:
    def __init__(
        self,
        arbitrator: Arbitrator,
        dispatcher: Dispatcher,
        team_lead: TeamLead,
        session_id: UUID,
        max_steps: int = 200,
    ):
        self._arb = arbitrator
        self._dispatcher = dispatcher
        self._team_lead = team_lead
        self._session_id = session_id
        self._team_id = team_lead.playbook.name
        self._ctx = ConductorContext(
            session_id=session_id, team_id=self._team_id
        )
        self._max_steps = max_steps

    async def run(self) -> None:
        """Run the session from the initial state to a terminal state."""
        await self._arb.open_session(
            self._session_id, initial_team_id=self._team_id
        )
        current = self._team_lead.initial_state
        step = 0
        while True:
            step += 1
            if step > self._max_steps:
                await self._arb.close_session(
                    self._session_id, SessionStatus.FAILED
                )
                raise RuntimeError(
                    f"Conductor exceeded max_steps={self._max_steps}"
                )

            state = self._team_lead.playbook.state(current)
            node = await self._arb.push_state(
                session_id=self._session_id,
                team_id=self._team_id,
                state_name=state.name,
                parent_node_id=self._ctx.parent_state_node_id,
            )
            prev_parent = self._ctx.parent_state_node_id
            self._ctx.parent_state_node_id = node.node_id
            await self._arb.emit_event(
                session_id=self._session_id,
                team_id=self._team_id,
                kind="state_enter",
                payload={"state": state.name},
            )

            self._ctx.pending_next_state = None
            await self._execute_entry_actions(state.entry_actions)
            if state.judgment is not None:
                await self._run_judgment(state.name, state.judgment)

            await self._arb.pop_state(node.node_id)
            self._ctx.parent_state_node_id = prev_parent

            if state.terminal:
                await self._arb.close_session(
                    self._session_id, SessionStatus.COMPLETED
                )
                return

            successors = self._team_lead.playbook.legal_successors(current)
            if not successors:
                await self._arb.close_session(
                    self._session_id, SessionStatus.FAILED
                )
                raise RuntimeError(
                    f"Non-terminal state {current!r} has no successors"
                )

            if self._ctx.pending_next_state is not None:
                next_state = self._ctx.pending_next_state
                self._ctx.pending_next_state = None
            elif len(successors) == 1:
                next_state = successors[0]
            else:
                raise RuntimeError(
                    f"State {current!r} has multiple successors {successors} "
                    f"but no judgment to choose"
                )
            self._team_lead.validate_transition(state.name, next_state)
            current = next_state

    async def _execute_entry_actions(
        self, actions: tuple[Action, ...]
    ) -> None:
        """Execute a state's entry actions.

        DispatchSpecialist actions are grouped and run concurrently; every
        other action runs sequentially, preserving declaration order.
        """
        i = 0
        while i < len(actions):
            action = actions[i]
            if isinstance(action, DispatchSpecialist):
                group: list[DispatchSpecialist] = []
                while i < len(actions) and isinstance(
                    actions[i], DispatchSpecialist
                ):
                    group.append(actions[i])  # type: ignore[arg-type]
                    i += 1
                if len(group) == 1:
                    await self._dispatch_specialist(group[0])
                else:
                    await asyncio.gather(
                        *(self._dispatch_specialist(g) for g in group)
                    )
                continue
            await self._execute_action(action)
            i += 1

    async def _dispatch_specialist(self, action: DispatchSpecialist) -> None:
        spec = self._team_lead.playbook.manifest.get(action.specialist_name)
        await run_specialist(
            arbitrator=self._arb,
            dispatcher=self._dispatcher,
            session_id=self._session_id,
            team_id=self._team_id,
            specialist=spec,
            context=self._ctx.specialty_context,
            parent_state_node_id=self._ctx.parent_state_node_id,
        )

    async def _execute_action(self, action: Action) -> None:
        if isinstance(action, EmitMessage):
            await self._arb.create_message(
                session_id=self._session_id,
                team_id=self._team_id,
                direction="out",
                type=action.type,
                body=action.body,
            )
            return
        if isinstance(action, WaitForUserInput):
            return
        if isinstance(action, JudgmentCall):
            await self._run_judgment(
                state_name=None, spec_name=action.spec_name
            )
            return
        if isinstance(action, PresentResults):
            results = await self._arb.list_results(
                self._session_id, self._team_id
            )
            lines = [action.header]
            ranked = self._ctx.specialty_context.get("ranked_candidates")
            if ranked:
                for i, name in enumerate(ranked, 1):
                    lines.append(f"{i}. {name}")
            else:
                for r in results:
                    for f in r.summary_json.get("findings", []):
                        lines.append(f"- {f.get('body', f)}")
            await self._arb.create_message(
                session_id=self._session_id,
                team_id=self._team_id,
                direction="out",
                type="notification",
                body="\n".join(lines),
            )
            gate = await self._arb.create_gate(
                session_id=self._session_id,
                team_id=self._team_id,
                category="confirm",
                options=["accept", "reject", "refine"],
            )
            await self._arb.resolve_gate(
                gate.gate_id, self._ctx.auto_gate_verdict
            )
            if self._ctx.auto_gate_verdict == "accept":
                self._ctx.pending_next_state = "done"
            else:
                self._ctx.pending_next_state = "gather_traits"
            return
        raise TypeError(f"Unknown action type: {type(action).__name__}")

    async def _run_judgment(
        self, state_name: str | None, spec_name: str
    ) -> None:
        spec = self._team_lead.playbook.judgment_specs.get(spec_name)
        if spec is None:
            raise KeyError(f"Judgment spec {spec_name!r} not declared")

        prompt = spec.prompt_template.format(
            **self._ctx.specialty_context,
            session_id=str(self._session_id),
        )
        dispatch_id = f"judg_{uuid.uuid4().hex[:8]}"
        agent = AgentDefinition(
            name=spec.agent_name,
            prompt=(
                "You are a team-lead judgment worker. "
                "Return JSON strictly matching the schema."
            ),
            logical_model=spec.logical_model,
        )
        correlation = DispatchCorrelation(
            session_id=self._session_id,
            team_id=self._team_id,
            agent_id=spec.agent_name,
            dispatch_id=dispatch_id,
        )

        async def sink(evt: dict[str, Any]) -> None:
            await self._arb.emit_event(
                session_id=self._session_id,
                team_id=self._team_id,
                kind=evt.get("kind", evt.get("type", "event")),
                payload=evt,
                agent_id=spec.agent_name,
                dispatch_id=dispatch_id,
            )

        try:
            result = await self._dispatcher.dispatch(
                agent=agent,
                prompt=prompt,
                logical_model=spec.logical_model,
                response_schema=spec.response_schema,
                correlation=correlation,
                event_sink=sink,
            )
        except DispatchError as e:
            await self._arb.emit_event(
                session_id=self._session_id,
                team_id=self._team_id,
                kind="judgment_failed",
                payload={"spec": spec_name, "error": str(e)},
            )
            return

        response = result.response
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                response = {}
        if not isinstance(response, dict):
            response = {}

        # Judgment responses may carry ranked_candidates for the aggregate
        # state and/or a next_state override for branching transitions.
        if "ranked_candidates" in response:
            self._ctx.specialty_context["ranked_candidates"] = response[
                "ranked_candidates"
            ]
        next_state = response.get("next_state")
        if next_state:
            legal = spec.legal_next_states
            if legal and next_state not in legal:
                await self._arb.emit_event(
                    session_id=self._session_id,
                    team_id=self._team_id,
                    kind="judgment_illegal_next_state",
                    payload={
                        "spec": spec_name,
                        "proposed": next_state,
                        "legal": legal,
                    },
                )
                return
            self._ctx.pending_next_state = next_state
