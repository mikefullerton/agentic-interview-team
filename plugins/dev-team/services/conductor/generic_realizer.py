"""Generic realizer for any roadmap whose primitives carry `specialist`
+ `speciality` fields resolvable against a `TeamManifest`.

The conductor calls `realize(arb, dispatcher, session_id, node_id)`;
this module's `make_generic_realizer(manifest)` returns such a callable.
Each primitive's work is:

  1. Look up the specialty by (specialist, speciality) on the manifest.
  2. Dispatch a worker-agent with a prompt composed of the specialty's
     `worker_focus` plus any upstream context (aggregated from `result`
     rows linked to upstream plan_nodes).
  3. Write a `result` row tagged with plan_node_id so downstream nodes
     can read it.

Limits:
  - Context threading is naive — every upstream result's `summary_json`
    is concatenated as JSON into the prompt. Large roadmaps will need
    smarter selection.
  - The worker response schema is open: `{"result": <arbitrary JSON>}`.
    Specialty authors can post-process in downstream nodes.
  - Verifier is not called here; that's a follow-up.
"""
from __future__ import annotations

import json
import uuid
from typing import Any
from uuid import UUID

from .arbitrator import Arbitrator
from .dispatcher import (
    AgentDefinition,
    DispatchCorrelation,
    Dispatcher,
)
from .team_loader import TeamManifest


_WORKER_SCHEMA = {
    "type": "object",
    "properties": {"result": {}},
    "required": ["result"],
}


def _worker_prompt(
    focus: str,
    description: str,
    upstream_results: list[dict[str, Any]],
) -> str:
    upstream_json = json.dumps(
        [
            {
                "plan_node_id": r.get("plan_node_id"),
                "specialist_id": r.get("specialist_id"),
                "summary": r.get("summary_json", {}),
            }
            for r in upstream_results
        ]
    )
    return (
        f"{focus}\n\n"
        f"Specialty description: {description}\n\n"
        f"Upstream results (results written by prior plan_nodes this node "
        f"depends on):\n{upstream_json}\n\n"
        'Return JSON: {"result": <your output as an object>} — the object '
        "shape is up to you but should directly serve downstream consumers."
    )


def make_generic_realizer(
    manifest: TeamManifest,
    *,
    team_id: str | None = None,
):
    """Return a `RealizePrimitive` callable bound to `manifest`.

    When the conductor hands a node to the returned realizer:
    - specialist/speciality must be set on the plan_node and appear in
      the manifest; otherwise the realizer raises a clear error.
    - An LLM dispatch runs via the conductor's dispatcher.
    - A `result` row is written with `plan_node_id=node_id`.
    """
    resolved_team_id = team_id or manifest.name

    async def realize(
        arbitrator: Arbitrator,
        dispatcher: Dispatcher,
        session_id: UUID,
        node_id: str,
    ) -> None:
        node = await arbitrator.get_plan_node(node_id)
        if node is None:
            raise RuntimeError(f"plan_node {node_id} not found")
        if not node.specialist or not node.speciality:
            raise RuntimeError(
                f"generic realizer needs node.specialist + "
                f"node.speciality set; got "
                f"({node.specialist!r}, {node.speciality!r}) "
                f"on {node_id!r}"
            )

        specialty = manifest.get_specialty(node.specialist, node.speciality)
        if specialty is None:
            raise RuntimeError(
                f"specialty {node.specialist}.{node.speciality} not found "
                f"in team manifest {manifest.name!r}"
            )

        # Pull upstream results — all results linked to deps of this node.
        deps = await arbitrator.list_dependencies_of(node_id)
        upstream_node_ids = {d.depends_on_id for d in deps}
        all_results = await arbitrator.list_results(
            session_id, team_id=resolved_team_id
        )
        upstream_results = [
            {
                "plan_node_id": r.plan_node_id,
                "specialist_id": r.specialist_id,
                "summary_json": r.summary_json,
            }
            for r in all_results
            if r.plan_node_id in upstream_node_ids
        ]

        prompt = _worker_prompt(
            focus=specialty.worker_focus,
            description=specialty.description,
            upstream_results=upstream_results,
        )
        agent_name = f"{node.specialist}-{node.speciality}-worker"
        agent = AgentDefinition(
            name=agent_name,
            prompt=(
                f"You are the worker for {node.specialist}.{node.speciality}. "
                "Respond with valid JSON only."
            ),
            logical_model=specialty.logical_model,
        )
        correlation = DispatchCorrelation(
            session_id=session_id,
            team_id=resolved_team_id,
            agent_id=agent_name,
            dispatch_id=f"disp_{uuid.uuid4().hex[:8]}",
        )

        async def sink(evt: dict[str, Any]) -> None:
            await arbitrator.emit_event(
                session_id=session_id,
                team_id=resolved_team_id,
                kind=evt.get("kind", evt.get("type", "event")),
                payload=evt,
                agent_id=agent_name,
                dispatch_id=correlation.dispatch_id,
                plan_node_id=node_id,
            )

        dispatch_result = await dispatcher.dispatch(
            agent=agent,
            prompt=prompt,
            logical_model=specialty.logical_model,
            response_schema=_WORKER_SCHEMA,
            correlation=correlation,
            event_sink=sink,
        )
        output = dispatch_result.response.get("result")
        await arbitrator.create_result(
            session_id=session_id,
            team_id=resolved_team_id,
            specialist_id=node.specialist,
            passed=True,
            summary={"result": output, "speciality": node.speciality},
            plan_node_id=node_id,
        )

    return realize
