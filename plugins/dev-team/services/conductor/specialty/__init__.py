"""Conductor-owned specialties — worker/verifier pairs the conductor
dispatches to make scheduling and meta-decisions about a session.

Per `docs/planning/2026-04-17-whats-next-specialty.md`, the conductor
owns its own specialties alongside (not inside) any team. The first is
`whats-next`; others can register here without changing the core runtime.
"""
from .base import (
    ACTION_ADVANCE_TO,
    ACTION_AWAIT_GATE,
    ACTION_AWAIT_REQUEST,
    ACTION_DECOMPOSE,
    ACTION_DONE,
    ACTION_PRESENT_RESULTS,
    ACTION_RE_DECOMPOSE,
    LEGAL_ACTIONS,
    ActionDecision,
    ConductorSpecialty,
    VerifierVerdict,
)
from .whats_next import WhatsNextSpecialty

__all__ = [
    "ACTION_ADVANCE_TO",
    "ACTION_AWAIT_GATE",
    "ACTION_AWAIT_REQUEST",
    "ACTION_DECOMPOSE",
    "ACTION_DONE",
    "ACTION_PRESENT_RESULTS",
    "ACTION_RE_DECOMPOSE",
    "LEGAL_ACTIONS",
    "ActionDecision",
    "ConductorSpecialty",
    "VerifierVerdict",
    "WhatsNextSpecialty",
]
