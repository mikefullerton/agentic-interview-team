"""plan_realizer — drive a team's planner to emit plan_node rows.

For each (specialist, speciality) in the team manifest, dispatch a
planner prompt under the agent name `<specialist>-<speciality>-planner`.
The planner returns a JSON object:

    {
      "plan_nodes": [
        {"title": "...", "node_kind": "primitive",
         "specialist": "...", "speciality": "..."}
      ],
      "depends_on": [{"from": "<title>", "to": "<title>"}]
    }

Every emitted node is written into the supplied roadmap. Edges resolve
by title — the planner is expected to use globally unique titles so
cross-speciality edges can point into other dispatches' nodes.

v1 emits primitive nodes only (§ "Decisions" in the atp-plan-command
design doc). Compound decomposition is a follow-up.
"""
from __future__ import annotations

import json
from typing import Any, Awaitable, Callable
from uuid import UUID

from .arbitrator import Arbitrator
from .arbitrator.models import NodeKind
from .dispatcher import (
    AgentDefinition,
    DispatchCorrelation,
    Dispatcher,
)
from .team_loader import SpecialtyDef, TeamManifest


PlanRealizer = Callable[
    [Arbitrator, Dispatcher, UUID, str],
    Awaitable[None],
]


def make_plan_realizer(manifest: TeamManifest, *, goal: str) -> PlanRealizer:
    """Return an async callable that drives planning for `manifest`.

    The callable: dispatches one planner per speciality, parses each
    response, and writes plan_nodes + edges into the roadmap.
    """

    async def realize(
        arbitrator: Arbitrator,
        dispatcher: Dispatcher,
        session_id: UUID,
        roadmap_id: str,
    ) -> None:
        title_to_node_id: dict[str, str] = {}
        pending_edges: list[tuple[str, str]] = []

        for specialist in manifest.specialists.values():
            for specialty in specialist.specialties.values():
                response = await _dispatch_planner(
                    arbitrator=arbitrator,
                    dispatcher=dispatcher,
                    session_id=session_id,
                    team_id=manifest.name,
                    goal=goal,
                    specialist_name=specialist.name,
                    specialty=specialty,
                )
                nodes = response.get("plan_nodes") or []
                for entry in nodes:
                    title = entry["title"]
                    if title in title_to_node_id:
                        raise ValueError(
                            f"duplicate plan_node title {title!r} in roadmap"
                        )
                    node = await arbitrator.create_plan_node(
                        roadmap_id=roadmap_id,
                        title=title,
                        node_kind=NodeKind(entry.get("node_kind", "primitive")),
                        specialist=entry.get("specialist"),
                        speciality=entry.get("speciality"),
                    )
                    title_to_node_id[title] = node.node_id
                for edge in response.get("depends_on") or []:
                    pending_edges.append((edge["from"], edge["to"]))

        for from_title, to_title in pending_edges:
            from_id = title_to_node_id.get(from_title)
            to_id = title_to_node_id.get(to_title)
            if from_id is None or to_id is None:
                raise ValueError(
                    f"depends_on edge references unknown title "
                    f"({from_title!r} → {to_title!r})"
                )
            await arbitrator.add_dependency(from_id, to_id)

    return realize


async def _dispatch_planner(
    *,
    arbitrator: Arbitrator,
    dispatcher: Dispatcher,
    session_id: UUID,
    team_id: str,
    goal: str,
    specialist_name: str,
    specialty: SpecialtyDef,
) -> dict[str, Any]:
    agent_name = f"{specialist_name}-{specialty.name}-planner"
    dispatch = await arbitrator.create_dispatch(
        session_id=session_id,
        team_id=team_id,
        agent_kind="planner",
        agent_name=agent_name,
        logical_model=specialty.logical_model,
    )
    prompt = _build_prompt(goal, specialist_name, specialty)
    agent = AgentDefinition(
        name=agent_name,
        prompt="Planner for a single speciality. Emit plan_nodes for your scope.",
        logical_model=specialty.logical_model,
    )
    correlation = DispatchCorrelation(
        session_id=session_id,
        team_id=team_id,
        agent_id=agent_name,
        dispatch_id=dispatch["dispatch_id"],
    )

    async def _sink(_event: dict) -> None:
        return None

    result = await dispatcher.dispatch(
        agent=agent,
        prompt=prompt,
        logical_model=specialty.logical_model,
        response_schema=None,
        correlation=correlation,
        event_sink=_sink,
    )
    await arbitrator.close_dispatch(dispatch["dispatch_id"], status="completed")

    if isinstance(result.response, dict):
        return result.response
    if isinstance(result.response, str):
        try:
            return json.loads(result.response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"{agent_name}: non-JSON response from dispatcher: {exc}"
            )
    raise ValueError(
        f"{agent_name}: expected dict response, got {type(result.response).__name__}"
    )


def _build_prompt(
    goal: str, specialist_name: str, specialty: SpecialtyDef
) -> str:
    return (
        f"Goal: {goal}\n\n"
        f"You are the planner voice of the {specialist_name} specialist, "
        f"focused on the {specialty.name} speciality.\n\n"
        f"Planner focus:\n{specialty.planner_focus}\n\n"
        "Return a single JSON object:\n"
        '  {"plan_nodes": [{"title": "<unique>", "node_kind": "primitive", '
        '"specialist": "...", "speciality": "..."}], '
        '"depends_on": [{"from": "<title>", "to": "<title>"}]}\n\n'
        "Titles must be unique across the whole roadmap — prefix them "
        "with your speciality to avoid collisions."
    )
