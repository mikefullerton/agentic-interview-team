"""Conductor error-path tests.

Each test constructs a minimal playbook that triggers one `raise` in
`conductor.py`, runs the conductor, and asserts the expected failure.
Every test also verifies the session row is closed with status FAILED
where that's the expected outcome — no silent hangs.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from services.conductor.arbitrator import (
    Arbitrator,
    SessionStatus,
)
from services.conductor.arbitrator.backends import SqliteBackend
from services.conductor.conductor import Conductor
from services.conductor.dispatcher import MockDispatcher
from services.conductor.playbook.types import (
    DispatchSpecialist,
    EmitMessage,
    JudgmentCall,
    JudgmentSpec,
    Manifest,
    RespondToRequest,
    SendRequest,
    SpecialistSpec,
    SpecialtySpec,
    State,
    TeamPlaybook,
    Transition,
    WriteProjectResource,
)
from services.conductor.team_lead import TeamLead


def _boot(tmp_path, playbook, dispatcher=None, aux=None):
    backend = SqliteBackend(tmp_path / "arb.sqlite")
    arb = Arbitrator(backend)
    conductor = Conductor(
        arbitrator=arb,
        dispatcher=dispatcher or MockDispatcher(),
        team_lead=TeamLead(playbook),
        session_id=uuid4(),
        aux_team_leads=[TeamLead(p) for p in (aux or [])],
    )
    return backend, arb, conductor


def test_multi_successor_without_judgment_fails(tmp_path, run_async):
    playbook = TeamPlaybook(
        name="t",
        states=[
            State(name="a"),
            State(name="b"),
            State(name="c"),
        ],
        transitions=[
            Transition("a", "b"),
            Transition("a", "c"),
        ],
        judgment_specs={},
        manifest=Manifest(),
        initial_state="a",
    )
    backend, arb, conductor = _boot(tmp_path, playbook)

    async def _t():
        await arb.start()
        with pytest.raises(RuntimeError) as exc_info:
            await conductor.run()
        assert "multiple successors" in str(exc_info.value)
        await arb.close()

    run_async(_t())


def test_max_steps_exceeded_fails_session(tmp_path, run_async):
    """A two-state loop should hit max_steps and fail, not hang."""
    playbook = TeamPlaybook(
        name="t",
        states=[
            State(name="a"),
            State(name="b"),
        ],
        transitions=[
            Transition("a", "b"),
            Transition("b", "a"),
        ],
        judgment_specs={},
        manifest=Manifest(),
        initial_state="a",
    )
    backend = SqliteBackend(tmp_path / "arb.sqlite")
    arb = Arbitrator(backend)
    conductor = Conductor(
        arbitrator=arb,
        dispatcher=MockDispatcher(),
        team_lead=TeamLead(playbook),
        session_id=uuid4(),
        max_steps=5,
    )

    async def _t():
        await arb.start()
        with pytest.raises(RuntimeError) as exc_info:
            await conductor.run()
        assert "max_steps" in str(exc_info.value)
        row = await backend.fetch_one(
            "session", {"session_id": str(conductor._session_id)}  # noqa: SLF001
        )
        assert row["status"] == SessionStatus.FAILED.value
        await arb.close()

    run_async(_t())


def test_non_terminal_with_no_successors_fails(tmp_path, run_async):
    playbook = TeamPlaybook(
        name="t",
        states=[State(name="dead_end")],  # not terminal, no transitions
        transitions=[],
        judgment_specs={},
        manifest=Manifest(),
        initial_state="dead_end",
    )
    backend, arb, conductor = _boot(tmp_path, playbook)

    async def _t():
        await arb.start()
        with pytest.raises(RuntimeError) as exc_info:
            await conductor.run()
        assert "no successors" in str(exc_info.value)
        row = await backend.fetch_one(
            "session", {"session_id": str(conductor._session_id)}  # noqa: SLF001
        )
        assert row["status"] == SessionStatus.FAILED.value
        await arb.close()

    run_async(_t())


def test_respond_to_request_outside_handler_raises(tmp_path, run_async):
    """RespondToRequest is only valid inside a handler state."""
    playbook = TeamPlaybook(
        name="t",
        states=[
            State(
                name="start",
                entry_actions=(RespondToRequest(response_data={"ok": True}),),
            ),
            State(name="done", terminal=True),
        ],
        transitions=[Transition("start", "done")],
        judgment_specs={},
        manifest=Manifest(),
        initial_state="start",
    )
    backend, arb, conductor = _boot(tmp_path, playbook)

    async def _t():
        await arb.start()
        with pytest.raises(RuntimeError) as exc_info:
            await conductor.run()
        assert "handler state" in str(exc_info.value)
        await arb.close()

    run_async(_t())


def test_write_project_resource_outside_handler_raises(tmp_path, run_async):
    playbook = TeamPlaybook(
        name="t",
        states=[
            State(
                name="start",
                entry_actions=(
                    WriteProjectResource(resource_type="schedule"),
                ),
            ),
            State(name="done", terminal=True),
        ],
        transitions=[Transition("start", "done")],
        judgment_specs={},
        manifest=Manifest(),
        initial_state="start",
    )
    backend, arb, conductor = _boot(tmp_path, playbook)

    async def _t():
        await arb.start()
        with pytest.raises(RuntimeError) as exc_info:
            await conductor.run()
        assert "handler state" in str(exc_info.value)
        await arb.close()

    run_async(_t())


def test_send_request_unknown_team_raises(tmp_path, run_async):
    playbook = TeamPlaybook(
        name="caller",
        states=[
            State(
                name="start",
                entry_actions=(
                    SendRequest(
                        kind="k.x",
                        to_team="not-registered",
                        input_data={},
                    ),
                ),
            ),
            State(name="done", terminal=True),
        ],
        transitions=[Transition("start", "done")],
        judgment_specs={},
        manifest=Manifest(),
        initial_state="start",
    )
    backend, arb, conductor = _boot(tmp_path, playbook)

    async def _t():
        await arb.start()
        with pytest.raises(KeyError) as exc_info:
            await conductor.run()
        assert "not-registered" in str(exc_info.value)
        await arb.close()

    run_async(_t())


def test_send_request_unknown_kind_raises(tmp_path, run_async):
    """Aux team registered but kind not handled → KeyError."""
    responder = TeamPlaybook(
        name="responder",
        states=[
            State(
                name="handler",
                entry_actions=(RespondToRequest(response_data={}),),
            ),
        ],
        transitions=[],
        judgment_specs={},
        manifest=Manifest(),
        initial_state="handler",
        request_handlers={"known.kind": "handler"},
    )
    caller = TeamPlaybook(
        name="caller",
        states=[
            State(
                name="start",
                entry_actions=(
                    SendRequest(
                        kind="unknown.kind",
                        to_team="responder",
                        input_data={},
                    ),
                ),
            ),
            State(name="done", terminal=True),
        ],
        transitions=[Transition("start", "done")],
        judgment_specs={},
        manifest=Manifest(),
        initial_state="start",
    )
    backend, arb, conductor = _boot(tmp_path, caller, aux=[responder])

    async def _t():
        await arb.start()
        with pytest.raises(KeyError) as exc_info:
            await conductor.run()
        assert "unknown.kind" in str(exc_info.value)
        await arb.close()

    run_async(_t())


def test_dispatch_error_in_specialist_marks_result_not_passed(
    tmp_path, run_async
):
    """A DispatchError from the specialist worker doesn't crash the session.

    Instead the result row gets passed=False and the session completes
    normally through the rest of its state machine.
    """
    schema = {
        "type": "object",
        "properties": {"findings": {"type": "array"}},
    }
    playbook = TeamPlaybook(
        name="t",
        states=[
            State(
                name="dispatch",
                entry_actions=(DispatchSpecialist("sp"),),
            ),
            State(name="done", terminal=True),
        ],
        transitions=[Transition("dispatch", "done")],
        judgment_specs={},
        manifest=Manifest(
            specialists=[
                SpecialistSpec(
                    name="sp",
                    specialties=[
                        SpecialtySpec(
                            name="speciality",
                            worker_agent="will-fail",
                            worker_prompt_template="p",
                            response_schema=schema,
                        )
                    ],
                )
            ]
        ),
        initial_state="dispatch",
    )
    # MockDispatcher with NO preset — every dispatch raises DispatchError.
    backend, arb, conductor = _boot(
        tmp_path, playbook, dispatcher=MockDispatcher()
    )

    async def _t():
        await arb.start()
        await conductor.run()
        row = await backend.fetch_one(
            "session", {"session_id": str(conductor._session_id)}  # noqa: SLF001
        )
        assert row["status"] == SessionStatus.COMPLETED.value
        results = await backend.fetch_all(
            "result", where={"session_id": str(conductor._session_id)}  # noqa: SLF001
        )
        assert len(results) == 1
        assert results[0]["passed"] == 0  # not passed
        # A specialty_failed event was emitted.
        events = await backend.fetch_all(
            "event", where={"session_id": str(conductor._session_id)}  # noqa: SLF001
        )
        kinds = {e["kind"] for e in events}
        assert "specialty_failed" in kinds
        await arb.close()

    run_async(_t())


def test_illegal_next_state_from_judgment_is_blocked(tmp_path, run_async):
    """Judgment returning a next_state not in legal_next_states is ignored.

    The conductor emits `judgment_illegal_next_state` and falls back to the
    default successor picker. With a single successor that's deterministic.
    """
    playbook = TeamPlaybook(
        name="t",
        states=[
            State(name="judge", judgment="pick"),
            State(name="done", terminal=True),
        ],
        transitions=[Transition("judge", "done")],
        judgment_specs={
            "pick": JudgmentSpec(
                prompt_template="prompt",
                response_schema={"type": "object"},
                legal_next_states=["done"],
                agent_name="judge-agent",
            )
        },
        manifest=Manifest(),
        initial_state="judge",
    )
    # Judgment returns an illegal next_state.
    dispatcher = MockDispatcher(
        {"judge-agent": {"next_state": "this-is-not-legal"}}
    )
    backend, arb, conductor = _boot(
        tmp_path, playbook, dispatcher=dispatcher
    )

    async def _t():
        await arb.start()
        await conductor.run()
        row = await backend.fetch_one(
            "session", {"session_id": str(conductor._session_id)}  # noqa: SLF001
        )
        assert row["status"] == SessionStatus.COMPLETED.value
        events = await backend.fetch_all(
            "event", where={"session_id": str(conductor._session_id)}  # noqa: SLF001
        )
        kinds = {e["kind"] for e in events}
        assert "judgment_illegal_next_state" in kinds
        await arb.close()

    run_async(_t())
