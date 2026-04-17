"""ConductorSpecialty protocol and the decision types it emits.

A conductor specialty is a worker (+ optional verifier) pair owned by
the conductor itself rather than any team. The conductor dispatches it
through the same `Dispatcher` plumbing teams use for their specialties.

Extensibility contract: new specialties (cost-watcher, replanner, etc.)
implement this protocol and are handed to `Conductor.run_roadmap` in a
list. The runtime calls `decide` on the specialty named `"whats-next"`
as its scheduling brain; other specialties are available for future
hooks but unused today.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


# Action enum kept as a string constant to stay close to the spec JSON.
ACTION_ADVANCE_TO = "advance-to"
ACTION_DECOMPOSE = "decompose"
ACTION_AWAIT_GATE = "await-gate"
ACTION_RE_DECOMPOSE = "re-decompose"
ACTION_AWAIT_REQUEST = "await-request"
ACTION_PRESENT_RESULTS = "present-results"
ACTION_DONE = "done"

LEGAL_ACTIONS = frozenset(
    {
        ACTION_ADVANCE_TO,
        ACTION_DECOMPOSE,
        ACTION_AWAIT_GATE,
        ACTION_RE_DECOMPOSE,
        ACTION_AWAIT_REQUEST,
        ACTION_PRESENT_RESULTS,
        ACTION_DONE,
    }
)


@dataclass(frozen=True)
class ActionDecision:
    """Output of a scheduling-style ConductorSpecialty.

    `action` is one of LEGAL_ACTIONS. `node_id` is the plan-node the
    action applies to (None for session-level actions like `done` /
    `present-results`). `deterministic` is True when the specialty
    computed the answer in Python without dispatching an LLM.
    """

    action: str
    node_id: str | None
    reason: str
    deterministic: bool

    def __post_init__(self) -> None:
        if self.action not in LEGAL_ACTIONS:
            raise ValueError(
                f"ActionDecision.action={self.action!r} not in {sorted(LEGAL_ACTIONS)}"
            )


@dataclass(frozen=True)
class VerifierVerdict:
    """Output of a verifier run over a worker's proposed decision."""

    verdict: str  # pass | verified | retry-with | fail
    alternative: ActionDecision | None
    reason: str


class ConductorSpecialty(Protocol):
    """Interface for conductor-owned specialties.

    Implementations must expose a stable `name` (used to route) and a
    `decide` coroutine that reads session state via the arbitrator and
    returns an `ActionDecision`.
    """

    name: str

    async def decide(
        self,
        arbitrator,  # service.conductor.arbitrator.Arbitrator
        dispatcher,  # service.conductor.dispatcher.Dispatcher
        session_id: UUID,
    ) -> ActionDecision: ...
