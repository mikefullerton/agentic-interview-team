"""MockDispatcher — pre-canned responses for tests and playbook authoring."""
from __future__ import annotations

import time
from typing import Any, Callable

from .base import (
    AgentDefinition,
    DispatchCorrelation,
    DispatchError,
    DispatchResult,
    Dispatcher,
    EventSink,
)


class MockDispatcher(Dispatcher):
    """Returns pre-canned responses keyed by agent name.

    Responses are either concrete values or callables that receive the
    rendered prompt and return a response. Use for unit tests and for
    wiring a playbook without making real LLM calls.
    """

    def __init__(
        self,
        responses: dict[str, Any] | None = None,
    ):
        self._responses: dict[str, Any] = responses or {}

    def set_response(
        self, agent_name: str, response: Any | Callable[[str], Any]
    ) -> None:
        self._responses[agent_name] = response

    async def dispatch(
        self,
        agent: AgentDefinition,
        prompt: str,
        logical_model: str,
        response_schema: dict | None,
        correlation: DispatchCorrelation,
        event_sink: EventSink,
        timeout_seconds: float = 300.0,
    ) -> DispatchResult:
        start = time.monotonic()
        if agent.name not in self._responses:
            raise DispatchError(
                f"MockDispatcher has no response for agent {agent.name!r}"
            )
        await event_sink(
            {
                "kind": "dispatch_start",
                "agent": agent.name,
                "dispatch_id": correlation.dispatch_id,
            }
        )
        raw = self._responses[agent.name]
        response = raw(prompt) if callable(raw) else raw
        await event_sink(
            {
                "kind": "dispatch_complete",
                "agent": agent.name,
                "dispatch_id": correlation.dispatch_id,
            }
        )
        return DispatchResult(
            response=response,
            duration_ms=int((time.monotonic() - start) * 1000),
            events=2,
            terminated_normally=True,
        )
