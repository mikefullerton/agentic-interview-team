"""Integration surface — transport-neutral host ↔ team protocol.

Design: docs/planning/2026-04-18-integration-surface-design.md
Plan:   docs/planning/2026-04-18-integration-surface-plan.md
"""
from .protocol import (
    Event,
    SessionHandle,
    SessionOptions,
    TeamSession,
    TurnIO,
)
from .event_schema import Violation, validate_event, validate_stream
from .in_process import InProcessSession, TeamRunner
from .stdio_ndjson import StdioSession, serve_stdio

__all__ = [
    "Event",
    "InProcessSession",
    "SessionHandle",
    "SessionOptions",
    "StdioSession",
    "TeamRunner",
    "TeamSession",
    "TurnIO",
    "Violation",
    "serve_stdio",
    "validate_event",
    "validate_stream",
]
