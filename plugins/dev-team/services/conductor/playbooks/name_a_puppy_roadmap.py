"""name-a-puppy as a roadmap + realizer — the new runtime shape.

Replaces the hand-written state machine in `name_a_puppy.py` with:
  1. A roadmap graph (6 primitive plan_nodes, one DAG of deps).
  2. A realizer function dispatched by `Conductor.run_roadmap` via
     `WhatsNextSpecialty`.

The realizer knows how to execute each node by looking at its
`speciality` field. Per-node work either runs deterministically (emit
a message, read a prior result) or dispatches an LLM worker through
the same `Dispatcher` the old playbook used.

Graph:
                  gather-traits
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   breed-names   lifestyle-names  temperament-names
        └──────────────┼──────────────┘
                       ▼
                   aggregate
                       │
                       ▼
                    present
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Any
from uuid import UUID

_PKG_ROOT = Path(__file__).resolve().parents[3]
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from services.conductor.arbitrator import Arbitrator  # noqa: E402
from services.conductor.arbitrator.models import NodeKind  # noqa: E402
from services.conductor.dispatcher import (  # noqa: E402
    AgentDefinition,
    DispatchCorrelation,
    Dispatcher,
)


TEAM_ID = "name-a-puppy-roadmap"


# ---------------------------------------------------------------------------
# Roadmap construction
# ---------------------------------------------------------------------------


NODE_IDS = [
    "gather-traits",
    "breed-names",
    "lifestyle-names",
    "temperament-names",
    "aggregate",
    "present",
]


# Each tuple is (node_id, title, speciality_tag). The speciality tag is
# what the realizer switches on.
_NODE_DEFS = [
    ("gather-traits", "Gather puppy traits", "gather"),
    ("breed-names", "Suggest breed-inspired names", "breed-name-suggester"),
    (
        "lifestyle-names",
        "Suggest lifestyle-inspired names",
        "lifestyle-name-suggester",
    ),
    (
        "temperament-names",
        "Suggest temperament-inspired names",
        "temperament-name-suggester",
    ),
    ("aggregate", "Rank all candidate names", "aggregator"),
    ("present", "Present ranked list to user", "presenter"),
]

_DEPS: list[tuple[str, str]] = [
    ("breed-names", "gather-traits"),
    ("lifestyle-names", "gather-traits"),
    ("temperament-names", "gather-traits"),
    ("aggregate", "breed-names"),
    ("aggregate", "lifestyle-names"),
    ("aggregate", "temperament-names"),
    ("present", "aggregate"),
]


async def build_roadmap(arbitrator: Arbitrator, title: str = "name-a-puppy") -> str:
    """Create the roadmap + plan_nodes + deps. Returns the roadmap_id."""
    roadmap = await arbitrator.create_roadmap(title)
    for node_id, node_title, speciality in _NODE_DEFS:
        await arbitrator.create_plan_node(
            roadmap_id=roadmap.roadmap_id,
            title=node_title,
            node_kind=NodeKind.PRIMITIVE,
            node_id=node_id,
            speciality=speciality,
        )
    for node, depends_on in _DEPS:
        await arbitrator.add_dependency(node, depends_on)
    return roadmap.roadmap_id


# ---------------------------------------------------------------------------
# Hardcoded puppy traits used by the gather-traits node.
#
# Phase 2 keeps gather-traits mechanical — no user interaction, no LLM.
# A follow-up will make it a real interview node. The shape of the
# "traits" record is what the naming specialties read.
# ---------------------------------------------------------------------------


DEFAULT_TRAITS: dict[str, Any] = {
    "breed": "golden retriever mix",
    "gender": "female",
    "coloring": "cream with white chest markings",
    "physical_features": "floppy ears, long tail, large paws",
    "temperament": "playful and affectionate",
    "quirks": "carries a stuffed duck everywhere",
    "family_history": "mother was a therapy dog",
}


# ---------------------------------------------------------------------------
# Realizer
# ---------------------------------------------------------------------------


_CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 5,
        }
    },
    "required": ["candidates"],
}


_RANKER_SCHEMA = {
    "type": "object",
    "properties": {
        "ranked_candidates": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 12,
        }
    },
    "required": ["ranked_candidates"],
}


_SPECIALTY_PROMPTS: dict[str, str] = {
    "breed-name-suggester": (
        "Suggest 3-5 names inspired by the puppy's breed(s). "
        "Traits: {traits_json}. "
        'Return JSON: {{"candidates": [names...]}}.'
    ),
    "lifestyle-name-suggester": (
        "Suggest 3-5 names inspired by an active outdoor lifestyle "
        "that fits this puppy. Traits: {traits_json}. "
        'Return JSON: {{"candidates": [names...]}}.'
    ),
    "temperament-name-suggester": (
        "Suggest 3-5 names matching the puppy's temperament and quirks. "
        "Traits: {traits_json}. "
        'Return JSON: {{"candidates": [names...]}}.'
    ),
}


_AGGREGATOR_PROMPT = (
    "Three specialties proposed candidate names. Rank the top 5 "
    "considering fit, memorability, and variety. "
    "Candidates:\n{candidates_json}\n"
    'Return JSON: {{"ranked_candidates": [names...]}}.'
)


async def _write_result(
    arbitrator: Arbitrator,
    session_id: UUID,
    node_id: str,
    specialist_id: str,
    summary: dict[str, Any],
) -> None:
    await arbitrator.create_result(
        session_id=session_id,
        team_id=TEAM_ID,
        specialist_id=specialist_id,
        passed=True,
        summary=summary,
        plan_node_id=node_id,
    )


async def _read_node_result(
    arbitrator: Arbitrator, session_id: UUID, node_id: str
) -> dict[str, Any] | None:
    results = await arbitrator.list_results(session_id, team_id=TEAM_ID)
    for r in results:
        if r.plan_node_id == node_id:
            return r.summary_json
    return None


async def _dispatch_candidate_worker(
    arbitrator: Arbitrator,
    dispatcher: Dispatcher,
    session_id: UUID,
    node_id: str,
    speciality: str,
    traits: dict[str, Any],
) -> dict[str, Any]:
    prompt_template = _SPECIALTY_PROMPTS[speciality]
    prompt = prompt_template.format(traits_json=json.dumps(traits))
    agent_name = speciality.replace("-suggester", "-worker")
    agent = AgentDefinition(
        name=agent_name,
        prompt="You are a focused naming worker. Respond with valid JSON only.",
        logical_model="fast-cheap",
    )
    correlation = DispatchCorrelation(
        session_id=session_id,
        team_id=TEAM_ID,
        agent_id=agent_name,
        dispatch_id=f"disp_{uuid.uuid4().hex[:8]}",
    )

    async def sink(evt: dict[str, Any]) -> None:
        await arbitrator.emit_event(
            session_id=session_id,
            team_id=TEAM_ID,
            kind=evt.get("kind", evt.get("type", "event")),
            payload=evt,
            agent_id=agent_name,
            dispatch_id=correlation.dispatch_id,
            plan_node_id=node_id,
        )

    result = await dispatcher.dispatch(
        agent=agent,
        prompt=prompt,
        logical_model="fast-cheap",
        response_schema=_CANDIDATE_SCHEMA,
        correlation=correlation,
        event_sink=sink,
    )
    return result.response


async def _dispatch_aggregator(
    arbitrator: Arbitrator,
    dispatcher: Dispatcher,
    session_id: UUID,
    node_id: str,
    all_candidates: list[str],
) -> list[str]:
    prompt = _AGGREGATOR_PROMPT.format(candidates_json=json.dumps(all_candidates))
    agent_name = "aggregator-worker"
    agent = AgentDefinition(
        name=agent_name,
        prompt="You rank puppy names. Respond with valid JSON only.",
        logical_model="balanced",
    )
    correlation = DispatchCorrelation(
        session_id=session_id,
        team_id=TEAM_ID,
        agent_id=agent_name,
        dispatch_id=f"disp_{uuid.uuid4().hex[:8]}",
    )

    async def sink(evt: dict[str, Any]) -> None:
        await arbitrator.emit_event(
            session_id=session_id,
            team_id=TEAM_ID,
            kind=evt.get("kind", evt.get("type", "event")),
            payload=evt,
            agent_id=agent_name,
            dispatch_id=correlation.dispatch_id,
            plan_node_id=node_id,
        )

    result = await dispatcher.dispatch(
        agent=agent,
        prompt=prompt,
        logical_model="balanced",
        response_schema=_RANKER_SCHEMA,
        correlation=correlation,
        event_sink=sink,
    )
    ranked = result.response.get("ranked_candidates", [])
    if not isinstance(ranked, list):
        raise RuntimeError(
            f"aggregator returned non-list ranked_candidates: {ranked!r}"
        )
    return [str(x) for x in ranked]


# ---------------------------------------------------------------------------
# Public realizer
# ---------------------------------------------------------------------------


async def realize(
    arbitrator: Arbitrator,
    dispatcher: Dispatcher,
    session_id: UUID,
    node_id: str,
) -> None:
    """Execute the work for a single plan_node in the puppy roadmap.

    Called by `Conductor.run_roadmap` between `running` and `done`
    state events. Writes a `result` row per node so downstream nodes
    can read upstream outputs.
    """
    node = await arbitrator.get_plan_node(node_id)
    if node is None:
        raise RuntimeError(f"plan_node {node_id} not found")
    speciality = node.speciality

    if speciality == "gather":
        # Phase 2: no real interview. Just record traits and emit a note.
        await arbitrator.create_message(
            session_id=session_id,
            team_id=TEAM_ID,
            direction="out",
            type="notification",
            body="Gathering puppy traits…",
            plan_node_id=node_id,
        )
        await _write_result(
            arbitrator,
            session_id,
            node_id,
            specialist_id="gather",
            summary={"traits": DEFAULT_TRAITS},
        )
        return

    if speciality in _SPECIALTY_PROMPTS:
        gather_result = await _read_node_result(
            arbitrator, session_id, "gather-traits"
        )
        traits = (
            (gather_result or {}).get("traits", DEFAULT_TRAITS)
            if gather_result
            else DEFAULT_TRAITS
        )
        resp = await _dispatch_candidate_worker(
            arbitrator,
            dispatcher,
            session_id,
            node_id,
            speciality,
            traits,
        )
        await _write_result(
            arbitrator,
            session_id,
            node_id,
            specialist_id=speciality.removesuffix("-suggester"),
            summary={"candidates": resp.get("candidates", [])},
        )
        return

    if speciality == "aggregator":
        all_candidates: list[str] = []
        for upstream in ("breed-names", "lifestyle-names", "temperament-names"):
            r = await _read_node_result(arbitrator, session_id, upstream)
            if r:
                all_candidates.extend(r.get("candidates", []))
        ranked = await _dispatch_aggregator(
            arbitrator, dispatcher, session_id, node_id, all_candidates
        )
        await _write_result(
            arbitrator,
            session_id,
            node_id,
            specialist_id="aggregator",
            summary={"ranked_candidates": ranked},
        )
        return

    if speciality == "presenter":
        agg = await _read_node_result(arbitrator, session_id, "aggregate")
        ranked = (agg or {}).get("ranked_candidates", [])
        body_lines = ["Top candidate names:"]
        for i, name in enumerate(ranked, 1):
            body_lines.append(f"{i}. {name}")
        body = "\n".join(body_lines)
        await arbitrator.create_message(
            session_id=session_id,
            team_id=TEAM_ID,
            direction="out",
            type="notification",
            body=body,
            plan_node_id=node_id,
        )
        await _write_result(
            arbitrator,
            session_id,
            node_id,
            specialist_id="presenter",
            summary={"presented_count": len(ranked)},
        )
        return

    raise RuntimeError(
        f"No realizer handler for speciality={speciality!r} "
        f"(node_id={node_id!r})"
    )
