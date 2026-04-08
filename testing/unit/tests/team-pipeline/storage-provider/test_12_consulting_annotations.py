"""Contract tests for consulting_annotations on team-result resource."""
import json
import pytest
from tp_helpers import run_arbitrator, run_ok, run_json, make_session


def _make_session():
    return make_session(playbook="generate", team_lead="review")


def _make_result(session_id, specialist):
    return run_json("result", "create", "--session", session_id, "--specialist", specialist)["result_id"]


def test_team_result_create_has_empty_consulting_annotations():
    session_id = _make_session()
    result_id = _make_result(session_id, "security")

    run_ok(
        "team-result", "create",
        "--session", session_id, "--result", result_id,
        "--specialist", "security", "--team", "authentication",
    )

    result = run_json(
        "team-result", "get",
        "--session", session_id, "--specialist", "security", "--team", "authentication",
    )
    assert result["consulting_annotations"] == []


def test_team_result_update_adds_consulting_annotation():
    session_id = _make_session()
    result_id = _make_result(session_id, "security")

    run_ok(
        "team-result", "create",
        "--session", session_id, "--result", result_id,
        "--specialist", "security", "--team", "token-handling",
    )

    annotation = json.dumps({
        "consultant": "cross-database-compatibility",
        "verdict": "NOT-APPLICABLE",
        "explanation": "Token handling has no cross-database implications",
    })

    run_ok(
        "team-result", "update",
        "--session", session_id, "--specialist", "security", "--team", "token-handling",
        "--add-consulting-annotation", annotation,
    )

    result = run_json(
        "team-result", "get",
        "--session", session_id, "--specialist", "security", "--team", "token-handling",
    )
    assert len(result["consulting_annotations"]) == 1
    assert result["consulting_annotations"][0]["consultant"] == "cross-database-compatibility"
    assert result["consulting_annotations"][0]["verdict"] == "NOT-APPLICABLE"


def test_team_result_update_appends_multiple_annotations():
    session_id = _make_session()
    result_id = _make_result(session_id, "security")

    run_ok(
        "team-result", "create",
        "--session", session_id, "--result", result_id,
        "--specialist", "security", "--team", "cors",
    )

    annotation1 = json.dumps({
        "consultant": "cross-database-compatibility",
        "verdict": "NOT-APPLICABLE",
        "explanation": "CORS has no cross-database implications",
    })
    annotation2 = json.dumps({
        "consultant": "sync-impact",
        "verdict": "VERIFIED",
        "findings": [{"concern": "CORS preflight", "assessment": "reviewed", "recommendation": "none"}],
        "summary": "CORS config compatible with sync endpoints",
    })

    run_ok(
        "team-result", "update",
        "--session", session_id, "--specialist", "security", "--team", "cors",
        "--add-consulting-annotation", annotation1,
    )
    run_ok(
        "team-result", "update",
        "--session", session_id, "--specialist", "security", "--team", "cors",
        "--add-consulting-annotation", annotation2,
    )

    result = run_json(
        "team-result", "get",
        "--session", session_id, "--specialist", "security", "--team", "cors",
    )
    assert len(result["consulting_annotations"]) == 2
    assert result["consulting_annotations"][0]["consultant"] == "cross-database-compatibility"
    assert result["consulting_annotations"][1]["consultant"] == "sync-impact"


def test_existing_team_results_without_annotations_still_work():
    """Backwards compatibility — team-results created before this feature."""
    session_id = _make_session()
    result_id = _make_result(session_id, "security")

    run_ok(
        "team-result", "create",
        "--session", session_id, "--result", result_id,
        "--specialist", "security", "--team", "input-validation",
    )
    run_ok(
        "team-result", "update",
        "--session", session_id, "--specialist", "security", "--team", "input-validation",
        "--status", "passed", "--iteration", "1",
    )

    result = run_json(
        "team-result", "get",
        "--session", session_id, "--specialist", "security", "--team", "input-validation",
    )
    assert result["status"] == "passed"
    assert result["consulting_annotations"] == []
