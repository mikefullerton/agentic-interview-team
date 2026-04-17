"""Stress — 50 specialists dispatched from one state run concurrently.

Each specialist has one specialty whose worker response is artificially
delayed by 10ms. If the conductor fans out via `asyncio.gather` the total
wall-clock is ~max(latencies), not ~sum. Budget: 500ms for 50 × 10ms.
"""
from __future__ import annotations

import asyncio
import time
from uuid import uuid4

import pytest

from services.conductor.arbitrator import Arbitrator, SessionStatus
from services.conductor.arbitrator.backends import SqliteBackend
from services.conductor.conductor import Conductor
from services.conductor.dispatcher import MockDispatcher
from services.conductor.playbook.types import (
    DispatchSpecialist,
    Manifest,
    SpecialistSpec,
    SpecialtySpec,
    State,
    TeamPlaybook,
    Transition,
)
from services.conductor.team_lead import TeamLead

pytestmark = pytest.mark.stress

N_SPECIALISTS = 50
LATENCY_S = 0.010
WALL_CLOCK_BUDGET_S = 0.5


class SlowMock(MockDispatcher):
    """MockDispatcher that pauses LATENCY_S before every worker response."""

    async def dispatch(self, *args, **kwargs):  # type: ignore[override]
        await asyncio.sleep(LATENCY_S)
        return await super().dispatch(*args, **kwargs)


def _build_playbook() -> TeamPlaybook:
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
    specialists = [
        SpecialistSpec(
            name=f"sp_{i}",
            specialties=[
                SpecialtySpec(
                    name=f"specialty_{i}",
                    worker_agent=f"worker_{i}",
                    worker_prompt_template="p",
                    response_schema=schema,
                )
            ],
        )
        for i in range(N_SPECIALISTS)
    ]
    dispatch_state = State(
        name="dispatch",
        entry_actions=tuple(
            DispatchSpecialist(f"sp_{i}") for i in range(N_SPECIALISTS)
        ),
    )
    return TeamPlaybook(
        name="fanout",
        states=[dispatch_state, State(name="done", terminal=True)],
        transitions=[Transition("dispatch", "done")],
        judgment_specs={},
        manifest=Manifest(specialists=specialists),
        initial_state="dispatch",
    )


def test_fifty_parallel_specialists_run_concurrently(tmp_path):
    async def _t():
        backend = SqliteBackend(tmp_path / "stress.sqlite")
        arb = Arbitrator(backend)
        await arb.start()

        dispatcher = SlowMock(
            {f"worker_{i}": {"ok": True} for i in range(N_SPECIALISTS)}
        )
        session_id = uuid4()
        conductor = Conductor(
            arbitrator=arb,
            dispatcher=dispatcher,
            team_lead=TeamLead(_build_playbook()),
            session_id=session_id,
        )

        start = time.monotonic()
        await conductor.run()
        elapsed = time.monotonic() - start
        assert elapsed < WALL_CLOCK_BUDGET_S, (
            f"Expected concurrent fan-out; took {elapsed:.2f}s "
            f"(serial would be {N_SPECIALISTS * LATENCY_S:.2f}s)"
        )

        row = await backend.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        assert row["status"] == SessionStatus.COMPLETED.value

        # N result rows, one per specialist.
        results = await arb.list_results(session_id)
        assert len(results) == N_SPECIALISTS
        assert {r.specialist_id for r in results} == {
            f"sp_{i}" for i in range(N_SPECIALISTS)
        }

        # Every specialty state pushed and popped (tree balanced).
        state_rows = await backend.fetch_all(
            "state", where={"session_id": str(session_id)}
        )
        specialty_nodes = [
            r
            for r in state_rows
            if r["state_name"].startswith("specialty:")
        ]
        assert len(specialty_nodes) == N_SPECIALISTS
        assert all(r["exit_date"] is not None for r in state_rows)
        assert await arb.active_state_nodes(session_id) == []

        await arb.close()

    asyncio.run(_t())
