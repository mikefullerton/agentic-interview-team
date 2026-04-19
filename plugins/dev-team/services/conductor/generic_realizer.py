"""Generic realizer — routes each plan_node's primitive through a specialist
subprocess. The specialist dispatches worker + verifier subagents internally
via the Task tool; the arbitrator records the parent specialist dispatch,
each child subagent dispatch, and the attempt grouping them.
"""
from __future__ import annotations

from uuid import UUID

from .arbitrator import Arbitrator
from .dispatcher import Dispatcher, SpecialistDispatcher
from .subagents import load_generic_subagents
from .team_loader import TeamManifest


def make_generic_realizer(
    manifest: TeamManifest,
    *,
    team_id: str | None = None,
):
    resolved_team_id = team_id or manifest.name
    subagent_defs = load_generic_subagents()

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
                f"generic realizer needs node.specialist + node.speciality; "
                f"got ({node.specialist!r}, {node.speciality!r}) on {node_id!r}"
            )
        specialty = manifest.get_specialty(node.specialist, node.speciality)
        if specialty is None:
            raise RuntimeError(
                f"specialty {node.specialist}.{node.speciality} not found "
                f"in team manifest {manifest.name!r}"
            )

        specialist_prompt = (
            f"You are the {node.specialist} specialist. Your job for this "
            f"plan_node is the {node.speciality} speciality.\n\n"
            "Use the speciality-worker subagent to do the work and the "
            "speciality-verifier subagent to check it. Return the final "
            "result plus an attempts array declaring the dispatch pairing "
            "and verdict."
        )

        sd = SpecialistDispatcher(inner=dispatcher, arbitrator=arbitrator)
        await sd.run_specialist(
            session_id=session_id,
            team_id=resolved_team_id,
            plan_node_id=node_id,
            specialist_name=node.specialist,
            specialist_prompt=specialist_prompt,
            worker_focus=specialty.worker_focus,
            verify_criteria=specialty.verify,
            logical_model=specialty.logical_model,
            subagent_defs=subagent_defs,
        )

    return realize
