"""Team-playbook declarative types — spec §5.5.

> **Deprecated for new teams.** The state-machine fields on `TeamPlaybook`
> (`states`, `transitions`, `judgment_specs`, `initial_state`) are
> superseded by the roadmap runtime (`Conductor.run_roadmap`). New teams
> should be authored as `teams/<name>/` markdown (see
> `services/conductor/team_loader.py`), not as TeamPlaybook Python.
>
> The `manifest` and `request_handlers` fields remain relevant.

Declarations, not programs. Authors express a team as data: states,
transitions, judgment specs, manifest, actions. No imperative business logic
in state declarations; actions are first-class value objects the conductor
executes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Action objects — executed by the conductor when a state is entered.
# ---------------------------------------------------------------------------


@dataclass
class Action:
    """Marker base class. Authors should treat action instances as immutable."""


@dataclass
class EmitMessage(Action):
    """Write a `message` row to the arbitrator.

    direction: "out" (team-lead → user). type: "notification" | "question".
    """

    body: str
    type: str = "notification"


@dataclass
class WaitForUserInput(Action):
    """Pause the state machine until the next user-direction message arrives."""

    prompt: str | None = None


@dataclass
class JudgmentCall(Action):
    """Invoke a named JudgmentSpec via the dispatcher.

    The response's `next_state` field drives the transition. The judgment
    spec's legal_next_states guards the transition's legality.
    """

    spec_name: str


@dataclass
class DispatchSpecialist(Action):
    """Dispatch a specialist by manifest name. Push a child state node."""

    specialist_name: str


@dataclass
class PresentResults(Action):
    """Aggregate result rows for this session and emit a final notification."""

    header: str = "Results"


@dataclass
class SendRequest(Action):
    """Create an inter-team request and wait for the response.

    The target team's playbook must declare a handler for `kind` via
    `request_handlers`. The response JSON is stored in the caller's
    specialty context under `response_context_key`.
    """

    kind: str
    to_team: str
    input_data: dict[str, Any] = field(default_factory=dict)
    response_context_key: str = "request_response"


@dataclass
class WriteProjectResource(Action):
    """Write a PM resource row from the active request's input_json.

    Valid only inside a handler state. The conductor reads
    `self._current_request.input_json` as kwargs for the matching
    arbitrator.create_* method and responds with the inserted row.
    """

    resource_type: str  # "schedule" | "todo" | "decision"


@dataclass
class RespondToRequest(Action):
    """Complete the currently-handled request with a response payload.

    Only valid inside a handler state. The conductor tracks the active
    request and the arbitrator validates the completion.
    """

    response_data: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------


@dataclass
class State:
    name: str
    entry_actions: tuple[Action, ...] = ()
    judgment: str | None = None  # name of a JudgmentSpec invoked on entry
    terminal: bool = False


@dataclass
class Transition:
    from_state: str
    to_state: str


@dataclass
class JudgmentSpec:
    prompt_template: str
    response_schema: dict[str, Any]
    legal_next_states: list[str]
    logical_model: str = "balanced"
    agent_name: str = "team-lead-judgment"


# ---------------------------------------------------------------------------
# Manifest — specialists and specialties the team uses
# ---------------------------------------------------------------------------


@dataclass
class SpecialtySpec:
    name: str
    worker_agent: str  # AgentDefinition.name
    worker_prompt_template: str
    response_schema: dict[str, Any]
    logical_model: str = "balanced"


@dataclass
class SpecialistSpec:
    name: str
    specialties: list[SpecialtySpec]


@dataclass
class Manifest:
    specialists: list[SpecialistSpec] = field(default_factory=list)

    def get(self, specialist_name: str) -> SpecialistSpec:
        for s in self.specialists:
            if s.name == specialist_name:
                return s
        raise KeyError(f"Specialist {specialist_name!r} not in manifest")


# ---------------------------------------------------------------------------
# TeamPlaybook
# ---------------------------------------------------------------------------


@dataclass
class TeamPlaybook:
    name: str
    states: list[State]
    transitions: list[Transition]
    judgment_specs: dict[str, JudgmentSpec]
    manifest: Manifest
    initial_state: str
    # kind → handler state name. Each entry is a declaration that this
    # team handles incoming requests of `kind` by running the named state.
    request_handlers: dict[str, str] = field(default_factory=dict)

    def state(self, name: str) -> State:
        for s in self.states:
            if s.name == name:
                return s
        raise KeyError(f"State {name!r} not declared")

    def legal_successors(self, from_state: str) -> list[str]:
        return [t.to_state for t in self.transitions if t.from_state == from_state]

    def is_legal_transition(self, from_state: str, to_state: str) -> bool:
        return to_state in self.legal_successors(from_state)
