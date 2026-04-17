"""Stress — a 1000-state linear playbook runs to completion.

Verifies the conductor's inner loop has no per-step allocation leaks or
quadratic behavior, and that the state tree push/pop discipline scales.
Wall-clock budget: 10 seconds on a laptop.
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
    Manifest,
    State,
    TeamPlaybook,
    Transition,
)
from services.conductor.team_lead import TeamLead

pytestmark = pytest.mark.stress

CHAIN_LEN = 1000
WALL_CLOCK_BUDGET_S = 10.0


def _linear_playbook(n: int) -> TeamPlaybook:
    states = [State(name=f"s{i}") for i in range(n - 1)]
    states.append(State(name=f"s{n - 1}", terminal=True))
    transitions = [Transition(f"s{i}", f"s{i + 1}") for i in range(n - 1)]
    return TeamPlaybook(
        name="chain",
        states=states,
        transitions=transitions,
        judgment_specs={},
        manifest=Manifest(),
        initial_state="s0",
    )


def test_thousand_state_linear_chain(tmp_path):
    async def _t():
        playbook = _linear_playbook(CHAIN_LEN)
        backend = SqliteBackend(tmp_path / "stress.sqlite")
        arb = Arbitrator(backend)
        await arb.start()
        session_id = uuid4()
        conductor = Conductor(
            arbitrator=arb,
            dispatcher=MockDispatcher(),
            team_lead=TeamLead(playbook),
            session_id=session_id,
            max_steps=CHAIN_LEN + 500,
        )

        start = time.monotonic()
        await conductor.run()
        elapsed = time.monotonic() - start
        assert elapsed < WALL_CLOCK_BUDGET_S, (
            f"1000-state chain took {elapsed:.2f}s, budget {WALL_CLOCK_BUDGET_S}s"
        )

        row = await backend.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        assert row["status"] == SessionStatus.COMPLETED.value

        # Every state pushed and popped.
        state_rows = await backend.fetch_all(
            "state", where={"session_id": str(session_id)}
        )
        assert len(state_rows) == CHAIN_LEN
        assert all(r["exit_date"] is not None for r in state_rows)
        assert await arb.active_state_nodes(session_id) == []

        # Every state_enter event present and in declaration order.
        events = await arb.list_events(session_id)
        enters = [
            e.payload_json["state"]
            for e in events
            if e.kind == "state_enter"
        ]
        assert enters == [f"s{i}" for i in range(CHAIN_LEN)]

        await arb.close()

    asyncio.run(_t())
