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
from typing import Any, Awaitable, Callable
from uuid import UUID

from .arbitrator import Arbitrator, SessionStatus
from .arbitrator.models import NodeStateEventType, Request
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
    RespondToRequest,
    SendRequest,
    WaitForUserInput,
    WriteProjectResource,
)
from .specialist_runner import run_specialist
from .specialty import (
    ACTION_ADVANCE_TO,
    ACTION_AWAIT_GATE,
    ACTION_AWAIT_REQUEST,
    ACTION_DECOMPOSE,
    ACTION_DONE,
    ACTION_PRESENT_RESULTS,
    ACTION_RE_DECOMPOSE,
    ConductorSpecialty,
)
from .specialty.whats_next import (
    _runnable_nodes as _compute_runnable_nodes,
    gather_context as _gather_roadmap_context,
)
from .team_lead import TeamLead


RealizePrimitive = Callable[
    [Arbitrator, Dispatcher, UUID, str], Awaitable[None]
]

DecomposeCompound = Callable[
    [Arbitrator, Dispatcher, UUID, str], Awaitable[None]
]

PresentResultsFn = Callable[
    [Arbitrator, Dispatcher, UUID], Awaitable[None]
]


async def _noop_realize_primitive(
    arbitrator: Arbitrator,
    dispatcher: Dispatcher,
    session_id: UUID,
    node_id: str,
) -> None:
    """Default realizer: does nothing. The conductor records running/done
    node state events around this call, so a noop realizer still produces
    the right node_state_event history for tests that only exercise walk
    order."""
    return None


async def _default_decompose(
    arbitrator: Arbitrator,
    dispatcher: Dispatcher,
    session_id: UUID,
    node_id: str,
) -> None:
    """Default decompose handler: marks the compound node `done` directly.

    Real decomposition expands a compound node by dispatching a
    specialist planning-mode worker that writes new plan_node children.
    The default here is a no-op placeholder so sessions that don't need
    real decomposition still run. Callers pass a real handler via
    `run_roadmap(decompose_compound=...)` when they need it.
    """
    return None


async def _default_present_results(
    arbitrator: Arbitrator,
    dispatcher: Dispatcher,
    session_id: UUID,
) -> None:
    """Default present-results handler: emits a summary notification."""
    await arbitrator.create_message(
        session_id=session_id,
        team_id="conductor",
        direction="out",
        type="notification",
        body="All roadmap nodes complete.",
    )


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
        team_lead: TeamLead | None,
        session_id: UUID,
        max_steps: int = 200,
        aux_team_leads: list[TeamLead] | None = None,
        conductor_team_id: str = "conductor",
    ):
        self._arb = arbitrator
        self._dispatcher = dispatcher
        self._team_lead = team_lead
        self._session_id = session_id
        self._team_id = (
            team_lead.playbook.name if team_lead is not None else conductor_team_id
        )
        self._ctx = ConductorContext(
            session_id=session_id, team_id=self._team_id
        )
        self._max_steps = max_steps
        # Secondary teams keyed by playbook name. Each one's declared
        # request_handlers get registered on the arbitrator at start.
        self._aux_team_leads: dict[str, TeamLead] = {
            t.playbook.name: t for t in (aux_team_leads or [])
        }
        self._current_request: Request | None = None
        self._active_team_id = self._team_id

    async def run(self) -> None:
        """Run the session from the initial state to a terminal state."""
        await self._arb.open_session(
            self._session_id, initial_team_id=self._team_id
        )
        self._register_cross_team_handlers()
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

    async def run_roadmap(
        self,
        specialties: list[ConductorSpecialty],
        realize_primitive: RealizePrimitive | None = None,
        decompose_compound: DecomposeCompound | None = None,
        present_results: PresentResultsFn | None = None,
        await_poll_seconds: float = 0.05,
    ) -> None:
        """Drive a roadmap-backed session via conductor-owned specialties.

        One specialty in `specialties` must be named `"whats-next"`; it's
        the scheduler. Other specialties are accepted for future hooks
        but not invoked by the phase-1 loop.

        `realize_primitive` is called when the scheduler returns
        `advance-to` for a primitive node. It runs whatever domain work
        the node requires (dispatch a specialty, mark it mechanically,
        etc.) between `running` and `done` state events. If None, a
        no-op realizer is used — useful for tests that only exercise
        the walk order.
        """
        scheduler: ConductorSpecialty | None = None
        for s in specialties:
            if s.name == "whats-next":
                scheduler = s
                break
        if scheduler is None:
            raise ValueError(
                "run_roadmap requires a specialty named 'whats-next'"
            )

        if realize_primitive is None:
            realize_primitive = _noop_realize_primitive
        if decompose_compound is None:
            decompose_compound = _default_decompose
        if present_results is None:
            present_results = _default_present_results

        await self._arb.open_session(
            self._session_id, initial_team_id=self._team_id
        )

        step = 0
        while True:
            step += 1
            if step > self._max_steps:
                await self._arb.close_session(
                    self._session_id, SessionStatus.FAILED
                )
                raise RuntimeError(
                    f"run_roadmap exceeded max_steps={self._max_steps}"
                )

            decision = await scheduler.decide(
                self._arb, self._dispatcher, self._session_id
            )

            await self._arb.emit_event(
                session_id=self._session_id,
                team_id=self._team_id,
                kind="whats_next_decision",
                payload={
                    "action": decision.action,
                    "node_id": decision.node_id,
                    "reason": decision.reason,
                    "deterministic": decision.deterministic,
                },
            )

            if decision.action == ACTION_DONE:
                await self._arb.close_session(
                    self._session_id, SessionStatus.COMPLETED
                )
                return

            if decision.action == ACTION_ADVANCE_TO:
                if decision.node_id is None:
                    raise RuntimeError(
                        "whats-next returned advance-to without node_id"
                    )
                # Parallel batch: two runnable primitives with no
                # inter-dependency (which by definition holds for any
                # two concurrently-runnable primitives) can be realized
                # concurrently. The scheduler's pick is always in the
                # batch; any other runnable primitives join it.
                ctx = await _gather_roadmap_context(
                    self._arb, self._session_id
                )
                runnable = [
                    n
                    for n in _compute_runnable_nodes(ctx)
                    if n["node_kind"] == "primitive"
                ]
                batch_ids: list[str] = [decision.node_id]
                for n in runnable:
                    if n["node_id"] != decision.node_id:
                        batch_ids.append(n["node_id"])
                await self._advance_primitive_batch(
                    batch_ids, realize_primitive
                )
                continue

            if decision.action in (ACTION_DECOMPOSE, ACTION_RE_DECOMPOSE):
                if decision.node_id is None:
                    raise RuntimeError(
                        f"{decision.action} returned without node_id"
                    )
                await self._arb.record_node_state_event(
                    node_id=decision.node_id,
                    event_type=NodeStateEventType.RUNNING,
                    actor="conductor",
                    session_id=self._session_id,
                )
                await decompose_compound(
                    self._arb,
                    self._dispatcher,
                    self._session_id,
                    decision.node_id,
                )
                await self._arb.record_node_state_event(
                    node_id=decision.node_id,
                    event_type=NodeStateEventType.DONE,
                    actor="conductor",
                    session_id=self._session_id,
                )
                continue

            if decision.action == ACTION_AWAIT_GATE:
                await self._poll_until(
                    self._is_gate_resolved, decision.node_id, await_poll_seconds
                )
                continue

            if decision.action == ACTION_AWAIT_REQUEST:
                await self._poll_until(
                    self._is_request_complete,
                    decision.node_id,
                    await_poll_seconds,
                )
                continue

            if decision.action == ACTION_PRESENT_RESULTS:
                await present_results(
                    self._arb, self._dispatcher, self._session_id
                )
                continue

            # Defensive fallback — any future action not covered above.
            await self._arb.close_session(
                self._session_id, SessionStatus.FAILED
            )
            raise NotImplementedError(
                f"run_roadmap does not yet handle action {decision.action!r}"
            )

    async def _poll_until(
        self,
        predicate: Callable[[str | None], Awaitable[bool]],
        subject: str | None,
        interval: float,
    ) -> None:
        """Sleep-poll until `predicate` returns True. Minimal implementation
        suitable for mock tests; a production driver will replace this with
        event-bus notifications so the conductor doesn't spin."""
        while not await predicate(subject):
            await asyncio.sleep(interval)

    async def _is_gate_resolved(self, plan_node_id: str | None) -> bool:
        storage = self._arb._storage
        rows = await storage.fetch_all(
            "gate", where={"session_id": str(self._session_id)}
        )
        if plan_node_id is not None:
            rows = [r for r in rows if r.get("plan_node_id") == plan_node_id]
        if not rows:
            # No matching gate — treat as resolved so the conductor
            # doesn't spin forever on a missing subject.
            return True
        return all(r.get("verdict") is not None for r in rows)

    async def _is_request_complete(self, plan_node_id: str | None) -> bool:
        storage = self._arb._storage
        rows = await storage.fetch_all(
            "request", where={"session_id": str(self._session_id)}
        )
        if plan_node_id is not None:
            rows = [r for r in rows if r.get("plan_node_id") == plan_node_id]
        if not rows:
            return True
        return all(
            r.get("status") in ("completed", "failed", "timeout")
            for r in rows
        )

    async def _advance_primitive_batch(
        self,
        node_ids: list[str],
        realize_primitive: RealizePrimitive,
    ) -> None:
        """Run the realizer for each node_id in parallel, with each run
        bracketed by running/done `node_state_event` rows."""

        async def _advance_one(node_id: str) -> None:
            await self._arb.record_node_state_event(
                node_id=node_id,
                event_type=NodeStateEventType.RUNNING,
                actor="conductor",
                session_id=self._session_id,
            )
            await realize_primitive(
                self._arb,
                self._dispatcher,
                self._session_id,
                node_id,
            )
            await self._arb.record_node_state_event(
                node_id=node_id,
                event_type=NodeStateEventType.DONE,
                actor="conductor",
                session_id=self._session_id,
            )

        await asyncio.gather(*(_advance_one(nid) for nid in node_ids))

    def _register_cross_team_handlers(self) -> None:
        """Register every aux team's declared request handlers on the arbitrator."""
        for team_id, aux in self._aux_team_leads.items():
            for kind, handler_state in aux.playbook.request_handlers.items():
                if kind not in self._arb._request_kinds:  # noqa: SLF001
                    # Permissive schemas for step 3; tighten per-kind later.
                    self._arb.register_request_kind(
                        kind,
                        input_schema={"type": "object"},
                        response_schema={"type": "object"},
                    )
                self._arb.register_request_handler(
                    team_id=team_id, kind=kind, handler_state_node=handler_state
                )

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
        if isinstance(action, SendRequest):
            await self._send_request(action)
            return
        if isinstance(action, WriteProjectResource):
            if self._current_request is None:
                raise RuntimeError(
                    "WriteProjectResource is only valid inside a handler state"
                )
            kwargs = dict(self._current_request.input_json)
            team_for_row = self._active_team_id
            if action.resource_type == "schedule":
                row = await self._arb.create_schedule_item(
                    session_id=self._session_id,
                    team_id=team_for_row,
                    **kwargs,
                )
            elif action.resource_type == "todo":
                row = await self._arb.create_todo_item(
                    session_id=self._session_id,
                    team_id=team_for_row,
                    **kwargs,
                )
            elif action.resource_type == "decision":
                row = await self._arb.create_decision_item(
                    session_id=self._session_id,
                    team_id=team_for_row,
                    **kwargs,
                )
            else:
                raise ValueError(
                    f"Unknown project resource type: {action.resource_type!r}"
                )
            # Strip session_id from the response so callers don't need UUID handling.
            response_row = {k: v for k, v in row.items() if k != "session_id"}
            await self._arb.complete_request(
                self._current_request.request_id, response_row
            )
            return
        if isinstance(action, RespondToRequest):
            if self._current_request is None:
                raise RuntimeError(
                    "RespondToRequest is only valid inside a handler state"
                )
            await self._arb.complete_request(
                self._current_request.request_id,
                dict(action.response_data),
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

    async def _send_request(self, action: SendRequest) -> None:
        """Create a request, run the target team's handler, store response."""
        aux = self._aux_team_leads.get(action.to_team)
        if aux is None:
            raise KeyError(
                f"No auxiliary team {action.to_team!r} registered on conductor"
            )
        handler_state_name = aux.playbook.request_handlers.get(action.kind)
        if handler_state_name is None:
            raise KeyError(
                f"Team {action.to_team!r} has no handler for kind {action.kind!r}"
            )

        request = await self._arb.create_request(
            session_id=self._session_id,
            from_team=self._team_id,
            to_team=action.to_team,
            kind=action.kind,
            input_data=dict(action.input_data),
        )
        # Enforce the serial-queue semantics from §7.4 even though we run
        # the handler inline — exercises the arbitrator's queue logic.
        ready = await self._arb.next_ready_request(self._session_id)
        if ready is None or ready.request_id != request.request_id:
            raise RuntimeError(
                "Arbitrator did not return the just-created request as ready"
            )

        handler_state = aux.playbook.state(handler_state_name)
        handler_node = await self._arb.push_state(
            session_id=self._session_id,
            team_id=action.to_team,
            state_name=f"handler:{handler_state_name}",
            parent_node_id=None,  # handlers form their own subtree root
        )
        prev_team = self._active_team_id
        prev_parent = self._ctx.parent_state_node_id
        prev_request = self._current_request
        self._active_team_id = action.to_team
        self._ctx.parent_state_node_id = handler_node.node_id
        self._current_request = ready
        try:
            for act in handler_state.entry_actions:
                await self._execute_action(act)
        finally:
            await self._arb.pop_state(handler_node.node_id)
            self._active_team_id = prev_team
            self._ctx.parent_state_node_id = prev_parent
            self._current_request = prev_request

        final = await self._arb.get_request(request.request_id)
        response = (final.response_json or {}) if final else {}
        self._ctx.specialty_context[action.response_context_key] = response

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
