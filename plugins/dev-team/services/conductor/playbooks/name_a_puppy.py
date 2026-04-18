"""name-a-puppy team playbook — legacy state-machine runtime (reference only).

> **Deprecated.** This module exercises `Conductor.run` + `TeamPlaybook`
> state machines, which are superseded by the roadmap runtime. The
> equivalent roadmap-driven version lives in `name_a_puppy_roadmap.py`
> and is what `/atp run puppynamingteam` drives. This file is retained
> so the existing end-to-end tests documenting the old runtime's
> behavior continue to pass; no new work should add similar playbooks.

Flow:
    start
      └─ gather_traits (loops via judgment, decides when to proceed)
           └─ dispatch_specialists (3 in parallel: breed, lifestyle, temperament)
                └─ aggregate (ranking judgment)
                     └─ present (gate: accept/reject/refine)
                          └─ done

The state tree has real depth here — `dispatch_specialists` spawns three
children, each of which spawns grandchildren for its specialty runs.
"""
from __future__ import annotations

import sys
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parents[3]
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from services.conductor.playbook.types import (  # noqa: E402
    DispatchSpecialist,
    EmitMessage,
    JudgmentSpec,
    Manifest,
    PresentResults,
    SpecialistSpec,
    SpecialtySpec,
    State,
    TeamPlaybook,
    Transition,
)


# ---------------------------------------------------------------------------
# Specialty schemas / prompts
# ---------------------------------------------------------------------------

_CANDIDATE_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 10,
        }
    },
    "required": ["candidates"],
}


BREED_SPECIALTY = SpecialtySpec(
    name="breed-name-suggester",
    worker_agent="breed-name-worker",
    worker_prompt_template=(
        "Suggest 5 puppy names inspired by popular dog breeds. "
        'Return JSON: {{"candidates": ["name1", "name2", ...]}}.'
    ),
    response_schema=_CANDIDATE_LIST_SCHEMA,
    logical_model="fast-cheap",
)

LIFESTYLE_SPECIALTY = SpecialtySpec(
    name="lifestyle-name-suggester",
    worker_agent="lifestyle-name-worker",
    worker_prompt_template=(
        "Suggest 5 puppy names inspired by an active outdoor lifestyle "
        '(hiking, camping, water, adventure). Return JSON: {{"candidates": [...] }}.'
    ),
    response_schema=_CANDIDATE_LIST_SCHEMA,
    logical_model="fast-cheap",
)

TEMPERAMENT_SPECIALTY = SpecialtySpec(
    name="temperament-name-suggester",
    worker_agent="temperament-name-worker",
    worker_prompt_template=(
        "Suggest 5 puppy names that fit a playful, friendly temperament. "
        'Return JSON: {{"candidates": [...] }}.'
    ),
    response_schema=_CANDIDATE_LIST_SCHEMA,
    logical_model="fast-cheap",
)


BREED_SPECIALIST = SpecialistSpec(
    name="breed", specialties=[BREED_SPECIALTY]
)
LIFESTYLE_SPECIALIST = SpecialistSpec(
    name="lifestyle", specialties=[LIFESTYLE_SPECIALTY]
)
TEMPERAMENT_SPECIALIST = SpecialistSpec(
    name="temperament", specialties=[TEMPERAMENT_SPECIALTY]
)


# ---------------------------------------------------------------------------
# Judgment specs
# ---------------------------------------------------------------------------

GATHER_TRAITS_JUDGMENT = JudgmentSpec(
    prompt_template=(
        "We are helping the user name a puppy. Decide whether we have enough "
        "context to start dispatching specialists, or whether we should ask "
        "another question first. Session: {session_id}. "
        'Return JSON: {{"next_state": "gather_traits" | "dispatch_specialists", '
        '"question": "optional follow-up question"}}.'
    ),
    response_schema={
        "type": "object",
        "properties": {
            "next_state": {
                "type": "string",
                "enum": ["gather_traits", "dispatch_specialists"],
            },
            "question": {"type": "string"},
        },
        "required": ["next_state"],
    },
    legal_next_states=["gather_traits", "dispatch_specialists"],
    logical_model="balanced",
    agent_name="team-lead-gather",
)

RANK_JUDGMENT = JudgmentSpec(
    prompt_template=(
        "Three specialists proposed candidate puppy names. Read the result "
        "rows and return a single ranked list of the top 5 names. "
        'Return JSON: {{"ranked_candidates": ["name1", "name2", ...], '
        '"next_state": "present"}}.'
    ),
    response_schema={
        "type": "object",
        "properties": {
            "ranked_candidates": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 10,
            },
            "next_state": {"type": "string", "enum": ["present"]},
        },
        "required": ["ranked_candidates", "next_state"],
    },
    legal_next_states=["present"],
    logical_model="balanced",
    agent_name="team-lead-aggregator",
)


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

STATES = [
    State(
        name="start",
        entry_actions=(
            EmitMessage(
                "Let's find a name for your puppy.", type="notification"
            ),
        ),
    ),
    State(
        name="gather_traits",
        entry_actions=(
            EmitMessage(
                "Tell me about your puppy — breed, lifestyle, temperament.",
                type="question",
            ),
        ),
        judgment="ask_next_question",
    ),
    State(
        name="dispatch_specialists",
        entry_actions=(
            DispatchSpecialist("breed"),
            DispatchSpecialist("lifestyle"),
            DispatchSpecialist("temperament"),
        ),
    ),
    State(
        name="aggregate",
        entry_actions=(),
        judgment="rank_candidates",
    ),
    State(
        name="present",
        entry_actions=(PresentResults("Top candidate names:"),),
    ),
    State(name="done", terminal=True),
]

TRANSITIONS = [
    Transition("start", "gather_traits"),
    Transition("gather_traits", "gather_traits"),  # loop
    Transition("gather_traits", "dispatch_specialists"),
    Transition("dispatch_specialists", "aggregate"),
    Transition("aggregate", "present"),
    Transition("present", "done"),
    Transition("present", "gather_traits"),  # on refine
]

JUDGMENT_SPECS = {
    "ask_next_question": GATHER_TRAITS_JUDGMENT,
    "rank_candidates": RANK_JUDGMENT,
}

MANIFEST = Manifest(
    specialists=[BREED_SPECIALIST, LIFESTYLE_SPECIALIST, TEMPERAMENT_SPECIALIST]
)

PLAYBOOK = TeamPlaybook(
    name="name-a-puppy",
    states=STATES,
    transitions=TRANSITIONS,
    judgment_specs=JUDGMENT_SPECS,
    manifest=MANIFEST,
    initial_state="start",
)
