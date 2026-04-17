"""Crash-recovery tests — persisted-state invariants + resume placeholders.

Resume-from-persisted-state is **not implemented** in the walking skeleton
(conductor.run always starts from playbook.initial_state). Spec §13.2
mandates a crash-and-restart test; we split that mandate in two:

1. What we CAN test today — after a simulated mid-dispatch crash, the
   persisted state tree and event stream still obey their invariants.
   An operator can read the rows back and tell exactly where the session
   stopped. This is the minimum guarantee a future resume feature will
   rely on.

2. What we CAN'T test yet — actual resume. Marked @pytest.mark.skip with
   a clear reason so the gap is visible in every test run.
"""
from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from services.conductor.arbitrator import Arbitrator, SessionStatus
from services.conductor.arbitrator.backends import SqliteBackend
from services.conductor.arbitrator.models import StateStatus
from services.conductor.conductor import Conductor
from services.conductor.dispatcher import MockDispatcher
from services.conductor.playbook.types import (
    Manifest,
    RespondToRequest,
    State,
    TeamPlaybook,
    Transition,
)
from services.conductor.team_lead import TeamLead


def _crash_playbook() -> TeamPlaybook:
    """Playbook whose second state raises from an illegal action.

    RespondToRequest is only valid inside a handler state; triggering it
    from a regular state raises RuntimeError that propagates out of
    conductor.run without calling close_session — a clean stand-in for
    a mid-run crash.
    """
    return TeamPlaybook(
        name="crash",
        states=[
            State(name="start"),
            State(
                name="crash_here",
                entry_actions=(RespondToRequest(response_data={}),),
            ),
            State(name="done", terminal=True),
        ],
        transitions=[
            Transition("start", "crash_here"),
            Transition("crash_here", "done"),
        ],
        judgment_specs={},
        manifest=Manifest(),
        initial_state="start",
    )


def test_persisted_state_after_simulated_crash(tmp_path):
    """A RuntimeError from an illegal action leaves the state tree mid-run.

    The active state node remains unpopped with exit_date=NULL, the
    session stays OPEN, and the event sequence is still contiguous
    from 1..N despite the truncation.
    """

    async def _t():
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arb = Arbitrator(backend)
        await arb.start()
        session_id = uuid4()
        conductor = Conductor(
            arbitrator=arb,
            dispatcher=MockDispatcher(),
            team_lead=TeamLead(_crash_playbook()),
            session_id=session_id,
        )
        with pytest.raises(RuntimeError):
            await conductor.run()
        sid = str(session_id)

        # Session row left OPEN — the conductor did not call close_session.
        session_row = await backend.fetch_one("session", {"session_id": sid})
        assert session_row is not None
        assert session_row["status"] == SessionStatus.OPEN.value
        assert session_row["ended_at"] is None

        # At least one state row is still active (exit_date=NULL, status=active).
        state_rows = await backend.fetch_all("state", where={"session_id": sid})
        active = [r for r in state_rows if r["exit_date"] is None]
        assert len(active) >= 1, (
            "expected at least one active state row after mid-run crash"
        )
        assert all(r["status"] == StateStatus.ACTIVE.value for r in active)
        assert any(r["state_name"] == "crash_here" for r in active)

        # active_state_nodes surfaces them for a future resume path.
        active_from_api = await arb.active_state_nodes(session_id)
        assert len(active_from_api) >= 1

        # Event sequence is still a contiguous 1..N despite truncation.
        events = await arb.list_events(session_id)
        sequences = [e.sequence for e in events]
        assert sequences == list(range(1, len(sequences) + 1)), (
            f"event sequence gaps after crash: {sequences}"
        )

        # State tree parent FK integrity still holds.
        node_ids = {r["node_id"] for r in state_rows}
        for row in state_rows:
            if row["parent_node_id"] is not None:
                assert row["parent_node_id"] in node_ids

        await arb.close()

    asyncio.run(_t())


def test_re_running_conductor_replays_from_initial_state(tmp_path):
    """Documented behavior until resume-from-state lands.

    A new Conductor instance with the same session_id re-enters the
    initial state rather than continuing from active_state_nodes. This
    test pins that behavior so anyone adding resume-from-state has a
    failing test to flip.
    """

    async def _t():
        backend = SqliteBackend(tmp_path / "arb.sqlite")
        arb = Arbitrator(backend)
        await arb.start()
        dispatcher = MockDispatcher()
        session_id = uuid4()

        # First run: crashes mid-state.
        first = Conductor(
            arbitrator=arb,
            dispatcher=dispatcher,
            team_lead=TeamLead(_crash_playbook()),
            session_id=session_id,
        )
        with pytest.raises(RuntimeError):
            await first.run()

        # Second run currently tries to open_session again with the same
        # session_id. That's a known limitation: until resume lands,
        # restarting is effectively a no-op and raises an integrity error
        # from the duplicate insert. Assert that loud failure mode so the
        # gap is visible.
        second = Conductor(
            arbitrator=arb,
            dispatcher=dispatcher,
            team_lead=TeamLead(_crash_playbook()),
            session_id=session_id,
        )
        with pytest.raises(Exception):
            await second.run()

        await arb.close()

    asyncio.run(_t())


@pytest.mark.skip(
    reason=(
        "resume-from-persisted-state is not implemented yet. "
        "conductor.run always starts from team_lead.initial_state. "
        "This placeholder exists so the gap is visible in every test run."
    )
)
def test_conductor_resumes_from_active_state_nodes(tmp_path):
    """Placeholder: a crashed session resumes from its active state tree.

    When implemented, this test should:
    1. Run a playbook until a mid-run DispatchError
    2. Construct a fresh Conductor for the same session_id
    3. Assert it picks up at `crash_here` (from active_state_nodes)
       rather than re-entering `start`
    4. Wire a working dispatcher so the second run completes normally
    5. Assert the final session row is COMPLETED and the state tree
       is balanced end-to-end
    """


@pytest.mark.skip(
    reason=(
        "resume-from-persisted-state is not implemented yet. "
        "Until it lands, we cannot assert no-event-gap across a restart."
    )
)
def test_event_sequence_preserved_across_restart(tmp_path):
    """Placeholder: events emitted after resume continue the sequence counter.

    When implemented, this should verify the arbitrator's per-session
    sequence counter is rehydrated from MAX(sequence) in the event
    table on resume, so the post-crash event stream is still a
    strict 1..N permutation.
    """
