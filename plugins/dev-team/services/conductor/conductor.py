"""Conductor main loop — roadmap runtime.

One conductor instance per session. `run_roadmap` drives a roadmap
graph by repeatedly asking a scheduling specialty (typically
`WhatsNextSpecialty`) what's next and dispatching the returned action.
Roadmap state and decisions are persisted to the arbitrator, so a
restart with the same session_id resumes from the last completed node.
"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable
from uuid import UUID

from .arbitrator import Arbitrator, SessionStatus
from .arbitrator.models import NodeStateEventType
from .dispatcher import Dispatcher
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
    """Default realizer: no-op. The conductor still records running/done
    node_state_events around this call, so tests that only exercise walk
    order don't need a real realizer."""
    return None


async def _default_decompose(
    arbitrator: Arbitrator,
    dispatcher: Dispatcher,
    session_id: UUID,
    node_id: str,
) -> None:
    """Default decompose handler: no-op. Real decomposition is pluggable."""
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


class Conductor:
    def __init__(
        self,
        arbitrator: Arbitrator,
        dispatcher: Dispatcher,
        session_id: UUID,
        *,
        max_steps: int = 200,
        conductor_team_id: str = "conductor",
        team_lead: Any = None,  # back-compat shim; accepts None
    ):
        self._arb = arbitrator
        self._dispatcher = dispatcher
        self._session_id = session_id
        self._team_id = conductor_team_id
        self._max_steps = max_steps

    async def run_roadmap(
        self,
        specialties: list[ConductorSpecialty],
        realize_primitive: RealizePrimitive | None = None,
        decompose_compound: DecomposeCompound | None = None,
        present_results: PresentResultsFn | None = None,
        await_poll_seconds: float = 0.05,
    ) -> None:
        """Drive a roadmap-backed session to completion."""
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
                    self._is_gate_resolved,
                    decision.node_id,
                    await_poll_seconds,
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
        while not await predicate(subject):
            await asyncio.sleep(interval)

    async def _is_gate_resolved(self, plan_node_id: str | None) -> bool:
        rows = await self._arb.list_gates(self._session_id)
        if plan_node_id is not None:
            rows = [r for r in rows if r.get("plan_node_id") == plan_node_id]
        if not rows:
            return True
        return all(r.get("verdict") is not None for r in rows)

    async def _is_request_complete(self, plan_node_id: str | None) -> bool:
        rows = await self._arb.list_requests(self._session_id)
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
