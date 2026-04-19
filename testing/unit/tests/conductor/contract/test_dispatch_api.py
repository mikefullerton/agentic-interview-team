"""Arbitrator create_dispatch/close_dispatch/create_attempt round-trip."""
from __future__ import annotations

import pytest

from services.conductor.arbitrator import Arbitrator
from services.conductor.arbitrator.backends import SqliteBackend


@pytest.fixture
def arb(tmp_path, run_async):
    a = Arbitrator(SqliteBackend(tmp_path / "arb.sqlite"))
    run_async(a.start())
    yield a
    run_async(a.close())


def test_create_dispatch_writes_row(arb, run_async, session_id):
    run_async(arb.open_session(session_id, initial_team_id="t"))
    d = run_async(arb.create_dispatch(
        session_id=session_id, team_id="t",
        agent_kind="specialist", agent_name="platform-database",
        logical_model="balanced",
    ))
    assert d["dispatch_id"]
    assert d["status"] == "running"
    assert d["parent_dispatch_id"] is None


def test_child_dispatch_links_to_parent(arb, run_async, session_id):
    run_async(arb.open_session(session_id, initial_team_id="t"))
    parent = run_async(arb.create_dispatch(
        session_id=session_id, team_id="t",
        agent_kind="specialist", agent_name="platform-database",
        logical_model="balanced",
    ))
    child = run_async(arb.create_dispatch(
        session_id=session_id, team_id="t",
        agent_kind="worker", agent_name="speciality-worker",
        logical_model="balanced",
        parent_dispatch_id=parent["dispatch_id"],
    ))
    assert child["parent_dispatch_id"] == parent["dispatch_id"]


def test_close_dispatch_sets_status_and_end(arb, run_async, session_id):
    run_async(arb.open_session(session_id, initial_team_id="t"))
    d = run_async(arb.create_dispatch(
        session_id=session_id, team_id="t",
        agent_kind="specialist", agent_name="sp", logical_model="balanced",
    ))
    closed = run_async(arb.close_dispatch(
        d["dispatch_id"], status="completed", concrete_model="claude-sonnet-4-6",
    ))
    assert closed["status"] == "completed"
    assert closed["end_date"] is not None
    assert closed["concrete_model"] == "claude-sonnet-4-6"


def test_create_attempt_links_worker_and_verifier(arb, run_async, session_id):
    run_async(arb.open_session(session_id, initial_team_id="t"))
    result = run_async(arb.create_result(
        session_id=session_id, team_id="t",
        specialist_id="platform-database", passed=True, summary={},
    ))
    w = run_async(arb.create_dispatch(
        session_id=session_id, team_id="t",
        agent_kind="worker", agent_name="speciality-worker",
        logical_model="balanced",
    ))
    v = run_async(arb.create_dispatch(
        session_id=session_id, team_id="t",
        agent_kind="verifier", agent_name="speciality-verifier",
        logical_model="balanced",
    ))
    att = run_async(arb.create_attempt(
        result_id=result.result_id, session_id=session_id,
        attempt_kind="speciality", attempt_number=1,
        worker_dispatch_id=w["dispatch_id"],
        verifier_dispatch_id=v["dispatch_id"],
        verdict="pass",
    ))
    assert att["attempt_id"]
    assert att["verdict"] == "pass"
    assert att["worker_dispatch_id"] == w["dispatch_id"]
