"""Contract tests for team-result resource."""
import pytest
from arbitrator_helpers import run_arbitrator, run_ok, run_json, make_session


def _make_session():
    return make_session(playbook="generate", team_lead="review")


def _make_result(session_id, specialist):
    return run_json("result", "create", "--session", session_id, "--specialist", specialist)["result_id"]


def test_team_result_create_returns_team_result_id():
    session_id = _make_session()
    result_id = _make_result(session_id, "security")

    result = run_json(
        "team-result", "create",
        "--session", session_id,
        "--result", result_id,
        "--specialist", "security",
        "--team", "authentication",
    )
    assert result["team_result_id"]


def test_team_result_create_sets_running_status_and_iteration_0():
    session_id = _make_session()
    result_id = _make_result(session_id, "security")

    run_ok(
        "team-result", "create",
        "--session", session_id, "--result", result_id, "--specialist", "security", "--team", "authorization",
    )

    result = run_json("team-result", "get", "--session", session_id, "--specialist", "security", "--team", "authorization")
    assert result["status"] == "running"
    assert str(result["iteration"]) == "0"
    assert result["specialist"] == "security"
    assert result["team_name"] == "authorization"


def test_team_result_update_changes_status_and_iteration():
    session_id = _make_session()
    result_id = _make_result(session_id, "security")

    run_ok("team-result", "create", "--session", session_id, "--result", result_id, "--specialist", "security", "--team", "token-handling")
    run_ok("team-result", "update", "--session", session_id, "--specialist", "security", "--team", "token-handling", "--status", "passed", "--iteration", "2")

    result = run_json("team-result", "get", "--session", session_id, "--specialist", "security", "--team", "token-handling")
    assert result["status"] == "passed"
    assert str(result["iteration"]) == "2"


def test_team_result_update_stores_verifier_feedback():
    session_id = _make_session()
    result_id = _make_result(session_id, "security")

    run_ok("team-result", "create", "--session", session_id, "--result", result_id, "--specialist", "security", "--team", "cors")
    run_ok(
        "team-result", "update",
        "--session", session_id, "--specialist", "security", "--team", "cors",
        "--status", "failed", "--iteration", "1", "--verifier-feedback", "Missing CORS allowlist check",
    )

    result = run_json("team-result", "get", "--session", session_id, "--specialist", "security", "--team", "cors")
    assert result["status"] == "failed"
    assert result["verifier_feedback"] == "Missing CORS allowlist check"


def test_team_result_list_returns_all_for_specialist():
    session_id = _make_session()
    result_id = _make_result(session_id, "security")

    run_ok("team-result", "create", "--session", session_id, "--result", result_id, "--specialist", "security", "--team", "authentication")
    run_ok("team-result", "create", "--session", session_id, "--result", result_id, "--specialist", "security", "--team", "authorization")
    run_ok("team-result", "create", "--session", session_id, "--result", result_id, "--specialist", "security", "--team", "cors")

    result = run_json("team-result", "list", "--session", session_id, "--specialist", "security")
    assert len(result) == 3


def test_team_result_list_filters_by_status():
    session_id = _make_session()
    result_id = _make_result(session_id, "security")

    run_ok("team-result", "create", "--session", session_id, "--result", result_id, "--specialist", "security", "--team", "authentication")
    run_ok("team-result", "create", "--session", session_id, "--result", result_id, "--specialist", "security", "--team", "authorization")
    run_ok("team-result", "update", "--session", session_id, "--specialist", "security", "--team", "authentication", "--status", "passed", "--iteration", "1")

    result = run_json("team-result", "list", "--session", session_id, "--specialist", "security", "--status", "passed")
    assert len(result) == 1
    assert result[0]["team_name"] == "authentication"


def test_team_result_list_filters_by_specialist():
    session_id = _make_session()
    sec_result = _make_result(session_id, "security")
    acc_result = _make_result(session_id, "accessibility")

    run_ok("team-result", "create", "--session", session_id, "--result", sec_result, "--specialist", "security", "--team", "authentication")
    run_ok("team-result", "create", "--session", session_id, "--result", acc_result, "--specialist", "accessibility", "--team", "accessibility")

    result = run_json("team-result", "list", "--session", session_id, "--specialist", "security")
    assert len(result) == 1


def test_team_result_list_returns_empty_for_new_session():
    session_id = _make_session()

    result = run_json("team-result", "list", "--session", session_id)
    assert len(result) == 0


def test_team_result_get_nonexistent_fails():
    session_id = _make_session()
    _make_result(session_id, "security")

    proc = run_arbitrator("team-result", "get", "--session", session_id, "--specialist", "security", "--team", "nonexistent")
    assert proc.returncode != 0


def test_team_result_update_nonexistent_fails():
    session_id = _make_session()
    _make_result(session_id, "security")

    proc = run_arbitrator("team-result", "update", "--session", session_id, "--specialist", "security", "--team", "nonexistent", "--status", "passed")
    assert proc.returncode != 0
