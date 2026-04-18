"""Roll-call — ping every role in a team via the integration surface.

Design: docs/planning/2026-04-18-rollcall-design.md
"""
from .discovery import RoleRef, discover_team, discover_teams
from .orchestrator import (
    ROLL_CALL_PROMPT,
    RollCallError,
    RollCallResult,
    roll_call,
)
from .formatting import render_json, render_table

__all__ = [
    "ROLL_CALL_PROMPT",
    "RoleRef",
    "RollCallError",
    "RollCallResult",
    "discover_team",
    "discover_teams",
    "render_json",
    "render_table",
    "roll_call",
]
