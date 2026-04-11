"""Dispatcher protocol — LLM vendor abstraction (spec §5.3).

Every dispatcher accepts a structured dispatch and returns a structured
result. Events stream to the caller-provided sink.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol
from uuid import UUID


@dataclass
class AgentDefinition:
    """One agent's static definition (markdown frontmatter + body)."""

    name: str
    prompt: str
    logical_model: str = "balanced"
    allowed_tools: list[str] = field(default_factory=list)


@dataclass
class DispatchCorrelation:
    session_id: UUID
    team_id: str
    agent_id: str
    dispatch_id: str


@dataclass
class DispatchResult:
    response: Any  # validated against response_schema if provided
    duration_ms: int
    events: int
    terminated_normally: bool
    error: str | None = None


class DispatchError(Exception):
    """Raised for typed dispatcher failures (crash, timeout, schema fail)."""


# An event sink is an async callable that receives parsed event dicts.
EventSink = Callable[[dict[str, Any]], Awaitable[None]]


class Dispatcher(Protocol):
    async def dispatch(
        self,
        agent: AgentDefinition,
        prompt: str,
        logical_model: str,
        response_schema: dict | None,
        correlation: DispatchCorrelation,
        event_sink: EventSink,
        timeout_seconds: float = 300.0,
    ) -> DispatchResult: ...
