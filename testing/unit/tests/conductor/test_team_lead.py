"""TeamLead — plan lookup and transition validation."""
from __future__ import annotations

import pytest

from services.conductor.playbook.types import (
    EmitMessage,
    Manifest,
    State,
    TeamPlaybook,
    Transition,
)
from services.conductor.team_lead import TeamLead


def _playbook() -> TeamPlaybook:
    return TeamPlaybook(
        name="t",
        states=[
            State(
                name="a",
                entry_actions=(EmitMessage("entering a"),),
            ),
            State(name="b"),
            State(name="c"),
            State(name="done", terminal=True),
        ],
        transitions=[
            Transition("a", "b"),
            Transition("a", "c"),
            Transition("b", "done"),
            Transition("c", "done"),
        ],
        judgment_specs={},
        manifest=Manifest(),
        initial_state="a",
    )


def test_initial_state_matches_playbook():
    lead = TeamLead(_playbook())
    assert lead.initial_state == "a"


def test_plan_for_returns_state_and_entry_actions():
    lead = TeamLead(_playbook())
    plan = lead.plan_for("a")
    assert plan.state.name == "a"
    assert len(plan.actions) == 1
    assert isinstance(plan.actions[0], EmitMessage)
    assert plan.actions[0].body == "entering a"


def test_plan_for_unknown_state_raises():
    lead = TeamLead(_playbook())
    with pytest.raises(KeyError):
        lead.plan_for("not-a-state")


def test_validate_transition_accepts_declared_edge():
    lead = TeamLead(_playbook())
    lead.validate_transition("a", "b")
    lead.validate_transition("a", "c")
    lead.validate_transition("b", "done")


def test_validate_transition_rejects_undeclared_edge():
    lead = TeamLead(_playbook())
    with pytest.raises(ValueError) as exc_info:
        lead.validate_transition("a", "done")
    msg = str(exc_info.value)
    assert "a" in msg and "done" in msg
    # Error message must surface the legal successors so authors can fix.
    assert "['b', 'c']" in msg or "'b'" in msg


def test_legal_successors_returns_declaration_order():
    pb = _playbook()
    assert pb.legal_successors("a") == ["b", "c"]
    assert pb.legal_successors("b") == ["done"]
    assert pb.legal_successors("done") == []


def test_is_legal_transition_matches_validate():
    pb = _playbook()
    assert pb.is_legal_transition("a", "b") is True
    assert pb.is_legal_transition("a", "done") is False
    assert pb.is_legal_transition("done", "a") is False
