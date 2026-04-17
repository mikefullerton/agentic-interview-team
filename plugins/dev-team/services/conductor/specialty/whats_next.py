"""`whats-next` — the conductor's scheduling specialty.

Reads the roadmap graph + live session state, then decides the next
action. When the situation is unambiguous (exactly one runnable node,
no crash state, no open gates) the answer is computed in Python and no
LLM is dispatched. Otherwise a worker+verifier pair runs via the
`Dispatcher` and returns a decision.

Phase 1 scope:
    - Only primitive plan_nodes are handled. Compound decomposition
      returns `decompose` but the conductor currently only advances
      primitives; richer action handling comes in a follow-up.
    - `await-request`, `re-decompose`, and `present-results` are legal
      actions the LLM can choose; the conductor handles them minimally.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from ..dispatcher import AgentDefinition, DispatchCorrelation, Dispatcher
from .base import (
    ACTION_ADVANCE_TO,
    ACTION_DECOMPOSE,
    ACTION_DONE,
    ACTION_PRESENT_RESULTS,
    LEGAL_ACTIONS,
    ActionDecision,
    ConductorSpecialty,
    VerifierVerdict,
)


TERMINAL_STATES = frozenset({"done", "failed", "superseded"})


@dataclass
class WhatsNextContext:
    """Everything the worker sees before deciding."""

    session_id: str
    roadmap_id: str | None
    plan_nodes: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[dict[str, Any]] = field(default_factory=list)
    latest_state_by_node: dict[str, str] = field(default_factory=dict)
    active_state_rows: list[dict[str, Any]] = field(default_factory=list)
    open_gates: list[dict[str, Any]] = field(default_factory=list)
    in_flight_requests: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Context gathering
# ---------------------------------------------------------------------------


async def gather_context(arbitrator, session_id: UUID) -> WhatsNextContext:
    """Pull the tables the worker / short-circuit needs into one bundle."""
    storage = arbitrator._storage  # pragmatic access; public helpers TBD
    session_row = await storage.fetch_one(
        "session", {"session_id": str(session_id)}
    )
    roadmap_id = session_row.get("roadmap_id") if session_row else None

    plan_nodes: list[dict[str, Any]] = []
    dependencies: list[dict[str, Any]] = []
    latest_state: dict[str, str] = {}
    if roadmap_id:
        plan_nodes = await storage.fetch_all(
            "plan_node", where={"roadmap_id": roadmap_id}
        )
        for n in plan_nodes:
            deps = await storage.fetch_all(
                "node_dependency", where={"node_id": n["node_id"]}
            )
            dependencies.extend(deps)
            events = await storage.fetch_all(
                "node_state_event",
                where={"node_id": n["node_id"]},
                order_by="event_date DESC",
                limit=1,
            )
            if events:
                latest_state[n["node_id"]] = events[0]["event_type"]

    active_state_rows = await storage.fetch_all(
        "state",
        where={"session_id": str(session_id), "status": "active"},
    )

    all_gates = await storage.fetch_all(
        "gate", where={"session_id": str(session_id)}
    )
    open_gates = [g for g in all_gates if g.get("verdict") is None]

    all_requests = await storage.fetch_all(
        "request", where={"session_id": str(session_id)}
    )
    in_flight_requests = [
        r
        for r in all_requests
        if r.get("status") in ("pending", "queued", "in-flight")
    ]

    return WhatsNextContext(
        session_id=str(session_id),
        roadmap_id=roadmap_id,
        plan_nodes=plan_nodes,
        dependencies=dependencies,
        latest_state_by_node=latest_state,
        active_state_rows=active_state_rows,
        open_gates=open_gates,
        in_flight_requests=in_flight_requests,
    )


# ---------------------------------------------------------------------------
# Deterministic short-circuit
# ---------------------------------------------------------------------------


def _runnable_nodes(ctx: WhatsNextContext) -> list[dict[str, Any]]:
    """Nodes not in a terminal state whose deps are all done."""
    deps_by_node: dict[str, list[str]] = {}
    for d in ctx.dependencies:
        deps_by_node.setdefault(d["node_id"], []).append(d["depends_on_id"])

    runnable: list[dict[str, Any]] = []
    for n in ctx.plan_nodes:
        nid = n["node_id"]
        state = ctx.latest_state_by_node.get(nid)
        if state in TERMINAL_STATES:
            continue
        prereqs = deps_by_node.get(nid, [])
        if any(
            ctx.latest_state_by_node.get(p) != "done" for p in prereqs
        ):
            continue
        # Skip nodes with an open gate on them.
        if any(g.get("plan_node_id") == nid for g in ctx.open_gates):
            continue
        runnable.append(n)
    return runnable


def _all_nodes_done(ctx: WhatsNextContext) -> bool:
    if not ctx.plan_nodes:
        return False
    return all(
        ctx.latest_state_by_node.get(n["node_id"]) == "done"
        for n in ctx.plan_nodes
    )


def deterministic_short_circuit(
    ctx: WhatsNextContext,
) -> ActionDecision | None:
    """Return a decision if the answer is unambiguous; else None.

    Deterministic cases:
      - No roadmap yet → None (LLM needed; or the caller handles empty).
      - All plan-nodes are `done` → `done` action.
      - Active state rows present (resume-in-progress or multi-team
        interleave) → None (worker decides, since interleaved state may
        have multiple interpretations).
      - Open session-level gate (no `plan_node_id`) → None.
      - Exactly one runnable primitive, no open gates on it, no in-flight
        request on it → `advance-to` deterministically.
    """
    if ctx.roadmap_id is None or not ctx.plan_nodes:
        return None

    if any(g.get("plan_node_id") is None for g in ctx.open_gates):
        return None

    if ctx.active_state_rows:
        return None

    if _all_nodes_done(ctx):
        return ActionDecision(
            action=ACTION_DONE,
            node_id=None,
            reason="all plan_nodes are done",
            deterministic=True,
        )

    runnable = _runnable_nodes(ctx)
    if len(runnable) != 1:
        return None

    node = runnable[0]
    nid = node["node_id"]
    if any(r.get("plan_node_id") == nid for r in ctx.in_flight_requests):
        return None

    if node["node_kind"] == "primitive":
        return ActionDecision(
            action=ACTION_ADVANCE_TO,
            node_id=nid,
            reason=f"only runnable primitive: {node['title']}",
            deterministic=True,
        )
    if node["node_kind"] == "compound":
        return ActionDecision(
            action=ACTION_DECOMPOSE,
            node_id=nid,
            reason=f"only runnable compound: {node['title']}",
            deterministic=True,
        )
    return None


# ---------------------------------------------------------------------------
# Prompt rendering
# ---------------------------------------------------------------------------


WORKER_PROMPT = (
    "You are the scheduler for an agentic session. Decide the single "
    "next action. If one node is clearly runnable and no ambiguity "
    "remains, set deterministic=true. Otherwise deterministic=false and "
    "explain briefly.\n\n"
    "Session: {session_id}\n"
    "Roadmap: {roadmap_id}\n"
    "Plan nodes: {plan_nodes_json}\n"
    "Dependencies: {dependencies_json}\n"
    "Latest state per node: {state_json}\n"
    "Active state rows: {active_json}\n"
    "Open gates: {gates_json}\n"
    "In-flight requests: {requests_json}\n\n"
    "Return JSON: "
    '{{"action": <one of '
    '"advance-to"|"decompose"|"await-gate"|"re-decompose"|"await-request"|"present-results"|"done">, '
    '"node_id": <plan_node_id or null>, '
    '"reason": <one sentence>, '
    '"deterministic": <true|false>}}.'
)


VERIFIER_PROMPT = (
    "The scheduler proposed this decision: {decision_json}\n\n"
    "Same input it saw:\n"
    "Plan nodes: {plan_nodes_json}\n"
    "Dependencies: {dependencies_json}\n"
    "Latest state per node: {state_json}\n"
    "Active state rows: {active_json}\n"
    "Open gates: {gates_json}\n"
    "In-flight requests: {requests_json}\n\n"
    "Check: (1) node exists and state matches; (2) all deps done; "
    "(3) no open gate or in-flight request is being ignored; "
    "(4) the decision handles any active-state rows correctly. "
    'Return JSON: {{"verdict": <"pass"|"verified"|"retry-with"|"fail">, '
    '"alternative": <null or same shape as the proposed decision>, '
    '"reason": <one sentence>}}.'
)


WORKER_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": sorted(LEGAL_ACTIONS)},
        "node_id": {"type": ["string", "null"]},
        "reason": {"type": "string", "minLength": 1, "maxLength": 280},
        "deterministic": {"type": "boolean"},
    },
    "required": ["action", "reason", "deterministic"],
}


VERIFIER_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["pass", "verified", "retry-with", "fail"],
        },
        "alternative": {"type": ["object", "null"]},
        "reason": {"type": "string", "minLength": 1, "maxLength": 280},
    },
    "required": ["verdict", "reason"],
}


def _render_worker_prompt(ctx: WhatsNextContext) -> str:
    return WORKER_PROMPT.format(
        session_id=ctx.session_id,
        roadmap_id=ctx.roadmap_id or "null",
        plan_nodes_json=json.dumps(
            [
                {
                    "node_id": n["node_id"],
                    "title": n["title"],
                    "node_kind": n["node_kind"],
                    "specialist": n.get("specialist"),
                    "speciality": n.get("speciality"),
                }
                for n in ctx.plan_nodes
            ]
        ),
        dependencies_json=json.dumps(
            [
                {"node_id": d["node_id"], "depends_on_id": d["depends_on_id"]}
                for d in ctx.dependencies
            ]
        ),
        state_json=json.dumps(ctx.latest_state_by_node),
        active_json=json.dumps(
            [
                {"state_id": s["state_id"], "state_name": s["state_name"]}
                for s in ctx.active_state_rows
            ]
        ),
        gates_json=json.dumps(
            [
                {"gate_id": g["gate_id"], "plan_node_id": g.get("plan_node_id")}
                for g in ctx.open_gates
            ]
        ),
        requests_json=json.dumps(
            [
                {
                    "request_id": r["request_id"],
                    "plan_node_id": r.get("plan_node_id"),
                    "kind": r.get("kind"),
                    "status": r.get("status"),
                }
                for r in ctx.in_flight_requests
            ]
        ),
    )


def _render_verifier_prompt(
    ctx: WhatsNextContext, proposed: ActionDecision
) -> str:
    decision_json = json.dumps(
        {
            "action": proposed.action,
            "node_id": proposed.node_id,
            "reason": proposed.reason,
            "deterministic": proposed.deterministic,
        }
    )
    return VERIFIER_PROMPT.format(
        decision_json=decision_json,
        plan_nodes_json=json.dumps(
            [
                {"node_id": n["node_id"], "title": n["title"]}
                for n in ctx.plan_nodes
            ]
        ),
        dependencies_json=json.dumps(
            [
                {"node_id": d["node_id"], "depends_on_id": d["depends_on_id"]}
                for d in ctx.dependencies
            ]
        ),
        state_json=json.dumps(ctx.latest_state_by_node),
        active_json=json.dumps(
            [{"state_id": s["state_id"]} for s in ctx.active_state_rows]
        ),
        gates_json=json.dumps(
            [
                {"gate_id": g["gate_id"], "plan_node_id": g.get("plan_node_id")}
                for g in ctx.open_gates
            ]
        ),
        requests_json=json.dumps(
            [
                {"request_id": r["request_id"], "status": r.get("status")}
                for r in ctx.in_flight_requests
            ]
        ),
    )


def _decision_from_response(resp: dict[str, Any]) -> ActionDecision:
    return ActionDecision(
        action=resp["action"],
        node_id=resp.get("node_id"),
        reason=resp.get("reason", ""),
        deterministic=bool(resp.get("deterministic", False)),
    )


def _verdict_from_response(resp: dict[str, Any]) -> VerifierVerdict:
    alt_payload = resp.get("alternative")
    alt = (
        _decision_from_response(alt_payload)
        if isinstance(alt_payload, dict) and "action" in alt_payload
        else None
    )
    return VerifierVerdict(
        verdict=resp.get("verdict", "fail"),
        alternative=alt,
        reason=resp.get("reason", ""),
    )


# ---------------------------------------------------------------------------
# Specialty
# ---------------------------------------------------------------------------


class WhatsNextSpecialty:
    """Scheduler specialty. Implements `ConductorSpecialty`."""

    name = "whats-next"

    def __init__(
        self,
        worker_agent: str = "whats-next-worker",
        verifier_agent: str = "whats-next-verifier",
        logical_model: str = "balanced",
    ):
        self.worker_agent = worker_agent
        self.verifier_agent = verifier_agent
        self.logical_model = logical_model

    async def decide(
        self,
        arbitrator,
        dispatcher: Dispatcher,
        session_id: UUID,
    ) -> ActionDecision:
        ctx = await gather_context(arbitrator, session_id)

        short = deterministic_short_circuit(ctx)
        if short is not None:
            return short

        worker_decision = await self._run_worker(
            ctx, arbitrator, dispatcher, session_id
        )
        if worker_decision.deterministic:
            # Worker self-reported deterministic — trust it without verifier.
            return worker_decision

        verdict = await self._run_verifier(
            ctx, worker_decision, arbitrator, dispatcher, session_id
        )
        if verdict.verdict in ("pass", "verified"):
            return worker_decision
        if verdict.verdict == "retry-with" and verdict.alternative is not None:
            return verdict.alternative
        # fail → return what the worker wanted, but mark with a reason
        # that makes the conductor open a gate. Phase 1: surface decision
        # as-is; conductor will see a non-advance action and handle.
        return worker_decision

    async def _run_worker(
        self,
        ctx: WhatsNextContext,
        arbitrator,
        dispatcher: Dispatcher,
        session_id: UUID,
    ) -> ActionDecision:
        prompt = _render_worker_prompt(ctx)
        agent = AgentDefinition(
            name=self.worker_agent,
            prompt="You are the conductor's scheduler. Respond with valid JSON only.",
            logical_model=self.logical_model,
        )
        correlation = DispatchCorrelation(
            session_id=session_id,
            team_id="conductor",
            agent_id=self.worker_agent,
            dispatch_id=f"disp_{uuid.uuid4().hex[:8]}",
        )

        async def sink(evt: dict[str, Any]) -> None:
            await arbitrator.emit_event(
                session_id=session_id,
                team_id="conductor",
                kind=evt.get("kind", evt.get("type", "event")),
                payload=evt,
                agent_id=self.worker_agent,
                dispatch_id=correlation.dispatch_id,
            )

        result = await dispatcher.dispatch(
            agent=agent,
            prompt=prompt,
            logical_model=self.logical_model,
            response_schema=WORKER_SCHEMA,
            correlation=correlation,
            event_sink=sink,
        )
        return _decision_from_response(result.response)

    async def _run_verifier(
        self,
        ctx: WhatsNextContext,
        proposed: ActionDecision,
        arbitrator,
        dispatcher: Dispatcher,
        session_id: UUID,
    ) -> VerifierVerdict:
        prompt = _render_verifier_prompt(ctx, proposed)
        agent = AgentDefinition(
            name=self.verifier_agent,
            prompt="You are the scheduler's verifier. Respond with valid JSON only.",
            logical_model=self.logical_model,
        )
        correlation = DispatchCorrelation(
            session_id=session_id,
            team_id="conductor",
            agent_id=self.verifier_agent,
            dispatch_id=f"disp_{uuid.uuid4().hex[:8]}",
        )

        async def sink(evt: dict[str, Any]) -> None:
            await arbitrator.emit_event(
                session_id=session_id,
                team_id="conductor",
                kind=evt.get("kind", evt.get("type", "event")),
                payload=evt,
                agent_id=self.verifier_agent,
                dispatch_id=correlation.dispatch_id,
            )

        result = await dispatcher.dispatch(
            agent=agent,
            prompt=prompt,
            logical_model=self.logical_model,
            response_schema=VERIFIER_SCHEMA,
            correlation=correlation,
            event_sink=sink,
        )
        return _verdict_from_response(result.response)


# Protocol conformance check (runtime assertion — imported at app start).
_: ConductorSpecialty = WhatsNextSpecialty()
