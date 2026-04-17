"""End-to-end: run the full name-a-puppy flow against MockDispatcher.

Covers: parallel specialist dispatch, judgment-driven transitions, state
tree push/pop discipline, aggregation ranking, gate resolution, session
completion.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))

from services.conductor.arbitrator import Arbitrator, SessionStatus  # noqa: E402
from services.conductor.arbitrator.backends import SqliteBackend  # noqa: E402
from services.conductor.conductor import Conductor  # noqa: E402
from services.conductor.dispatcher import MockDispatcher  # noqa: E402
from services.conductor.playbook import load_playbook  # noqa: E402
from services.conductor.team_lead import TeamLead  # noqa: E402


PLAYBOOK_PATH = (
    REPO_ROOT
    / "plugins"
    / "dev-team"
    / "services"
    / "conductor"
    / "playbooks"
    / "name_a_puppy.py"
)


def _build_dispatcher() -> MockDispatcher:
    return MockDispatcher(
        {
            "team-lead-gather": {"next_state": "dispatch_specialists"},
            "team-lead-aggregator": {
                "ranked_candidates": ["Luna", "Scout", "Rex", "Daisy", "Biscuit"],
                "next_state": "present",
            },
            "breed-name-worker": {"candidates": ["Rex", "Dash", "Biscuit"]},
            "lifestyle-name-worker": {"candidates": ["Scout", "River", "Sage"]},
            "temperament-name-worker": {"candidates": ["Luna", "Daisy", "Ollie"]},
        }
    )


def test_full_name_a_puppy_end_to_end(tmp_path):
    async def _t():
        playbook = load_playbook(PLAYBOOK_PATH)
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arbitrator = Arbitrator(backend)
        await arbitrator.start()
        dispatcher = _build_dispatcher()
        team_lead = TeamLead(playbook)
        session_id = uuid4()
        conductor = Conductor(arbitrator, dispatcher, team_lead, session_id)

        await conductor.run()

        row = await backend.fetch_one("session", {"session_id": str(session_id)})
        assert row is not None
        assert row["status"] == SessionStatus.COMPLETED.value

        # Three specialists, three results.
        results = await arbitrator.list_results(session_id)
        assert {r.specialist_id for r in results} == {
            "breed",
            "lifestyle",
            "temperament",
        }
        assert all(r.passed for r in results)

        # Ranked list appears in the final present notification.
        messages = await arbitrator.list_messages(session_id)
        bodies = [m.body for m in messages]
        present_body = bodies[-1]
        assert "Top candidate names:" in present_body
        for i, name in enumerate(
            ["Luna", "Scout", "Rex", "Daisy", "Biscuit"], 1
        ):
            assert f"{i}. {name}" in present_body

        # Gate was resolved accept → done.
        gate_rows = await backend.fetch_all(
            "gate", where={"session_id": str(session_id)}
        )
        assert len(gate_rows) == 1
        assert gate_rows[0]["verdict"] == "accept"
        assert gate_rows[0]["verdict_date"] is not None

        # State tree: every node popped (no active nodes).
        active = await arbitrator.active_state_nodes(session_id)
        assert active == []

        # State tree has depth: specialist nodes have specialty children.
        all_state_rows = await backend.fetch_all(
            "state", where={"session_id": str(session_id)}
        )
        specialist_nodes = [
            r for r in all_state_rows if r["state_name"].startswith("specialist:")
        ]
        assert len(specialist_nodes) == 3
        specialty_nodes = [
            r for r in all_state_rows if r["state_name"].startswith("specialty:")
        ]
        assert len(specialty_nodes) == 3
        # Each specialty's parent should be one of the specialist nodes.
        specialist_ids = {n["node_id"] for n in specialist_nodes}
        for sn in specialty_nodes:
            assert sn["parent_node_id"] in specialist_ids

        # Top-level state_enter events hit all declared states.
        events = await arbitrator.list_events(session_id)
        state_enters = [e for e in events if e.kind == "state_enter"]
        entered = [e.payload_json["state"] for e in state_enters]
        assert entered == [
            "start",
            "gather_traits",
            "dispatch_specialists",
            "aggregate",
            "present",
            "done",
        ]

        await arbitrator.close()

    asyncio.run(_t())


def test_gather_traits_loops_once_then_proceeds(tmp_path):
    """Judgment returns gather_traits once then dispatch_specialists."""

    async def _t():
        playbook = load_playbook(PLAYBOOK_PATH)
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arbitrator = Arbitrator(backend)
        await arbitrator.start()
        dispatcher = _build_dispatcher()

        call_count = {"n": 0}

        def gather_response(_prompt: str) -> dict:
            call_count["n"] += 1
            if call_count["n"] == 1:
                return {"next_state": "gather_traits"}
            return {"next_state": "dispatch_specialists"}

        dispatcher.set_response("team-lead-gather", gather_response)

        team_lead = TeamLead(playbook)
        session_id = uuid4()
        conductor = Conductor(arbitrator, dispatcher, team_lead, session_id)
        await conductor.run()

        # gather_traits entered twice.
        events = await arbitrator.list_events(session_id)
        entered = [
            e.payload_json["state"]
            for e in events
            if e.kind == "state_enter"
        ]
        assert entered.count("gather_traits") == 2
        assert call_count["n"] == 2
        await arbitrator.close()

    asyncio.run(_t())


def test_parallel_dispatch_is_concurrent(tmp_path):
    """Three DispatchSpecialist actions run in parallel, not serially."""

    async def _t():
        import time

        playbook = load_playbook(PLAYBOOK_PATH)
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arbitrator = Arbitrator(backend)
        await arbitrator.start()
        dispatcher = _build_dispatcher()

        # Each specialty sleeps 100ms before responding. If serial, total is
        # ~300ms for the three dispatches; if concurrent, ~100ms.
        async def slow_response(candidates):
            await asyncio.sleep(0.1)
            return {"candidates": candidates}

        # We can't use async callables in MockDispatcher's sync path, so
        # we instead add an artificial delay via a custom dispatcher subclass.
        class SlowMock(MockDispatcher):
            async def dispatch(self, *args, **kwargs):  # type: ignore[override]
                agent = kwargs.get("agent") or args[0]
                if agent.name.endswith("-name-worker"):
                    await asyncio.sleep(0.1)
                return await super().dispatch(*args, **kwargs)

        slow = SlowMock(
            {
                "team-lead-gather": {"next_state": "dispatch_specialists"},
                "team-lead-aggregator": {
                    "ranked_candidates": ["A", "B", "C"],
                    "next_state": "present",
                },
                "breed-name-worker": {"candidates": ["A"]},
                "lifestyle-name-worker": {"candidates": ["B"]},
                "temperament-name-worker": {"candidates": ["C"]},
            }
        )
        team_lead = TeamLead(playbook)
        session_id = uuid4()
        conductor = Conductor(arbitrator, slow, team_lead, session_id)
        start = time.monotonic()
        await conductor.run()
        elapsed = time.monotonic() - start
        # Generous bound: concurrent should be well under 0.25s; serial
        # would be > 0.30s.
        assert elapsed < 0.25, f"Expected concurrent dispatch; took {elapsed:.2f}s"
        await arbitrator.close()

    asyncio.run(_t())
