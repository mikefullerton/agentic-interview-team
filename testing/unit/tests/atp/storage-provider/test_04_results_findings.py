"""Contract tests for result and finding resources."""
import pytest
from tp_helpers import run_arbitrator, run_ok, run_json, make_session


def _make_session():
    return make_session(playbook="interview", team_lead="interview")


def test_result_create_returns_result_id():
    session_id = _make_session()
    result = run_json("result", "create", "--session", session_id, "--specialist", "security")
    assert result["result_id"]


def test_result_get_returns_all_fields():
    session_id = _make_session()
    created = run_json("result", "create", "--session", session_id, "--specialist", "performance")
    result_id = created["result_id"]

    result = run_json("result", "get", "--result", result_id)
    assert result["specialist"] == "performance"
    assert result["session_id"] == session_id
    assert result["result_id"] == result_id
    assert result["creation_date"]


def test_result_list_returns_results_for_session():
    session_id = _make_session()
    run_ok("result", "create", "--session", session_id, "--specialist", "security")
    run_ok("result", "create", "--session", session_id, "--specialist", "accessibility")

    result = run_json("result", "list", "--session", session_id)
    assert len(result) >= 2


def test_result_list_filters_by_specialist():
    session_id = _make_session()
    run_ok("result", "create", "--session", session_id, "--specialist", "security")
    run_ok("result", "create", "--session", session_id, "--specialist", "performance")

    result = run_json("result", "list", "--session", session_id, "--specialist", "security")
    assert len(result) == 1
    assert result[0]["specialist"] == "security"


def test_finding_create_returns_finding_id():
    session_id = _make_session()
    result_id = run_json("result", "create", "--session", session_id, "--specialist", "security")["result_id"]

    result = run_json(
        "finding", "create",
        "--session", session_id,
        "--result", result_id,
        "--specialist", "security",
        "--category", "vulnerability",
        "--severity", "high",
        "--title", "SQL injection risk",
        "--detail", "User input is not sanitized before query execution",
    )
    assert result["finding_id"]


def test_finding_get_returns_all_fields():
    session_id = _make_session()
    result_id = run_json("result", "create", "--session", session_id, "--specialist", "security")["result_id"]

    created = run_json(
        "finding", "create",
        "--session", session_id,
        "--result", result_id,
        "--specialist", "security",
        "--category", "vulnerability",
        "--severity", "critical",
        "--title", "Hardcoded credentials",
        "--detail", "API key found in source code",
    )
    finding_id = created["finding_id"]

    result = run_json("finding", "get", "--finding", finding_id)
    assert result["specialist"] == "security"
    assert result["session_id"] == session_id
    assert result["result_id"] == result_id
    assert result["category"] == "vulnerability"
    assert result["severity"] == "critical"
    assert result["title"] == "Hardcoded credentials"
    assert result["detail"] == "API key found in source code"
    assert result["creation_date"]
    assert result["linked_artifacts"] == []


def test_finding_list_returns_findings():
    session_id = _make_session()
    result_id = run_json("result", "create", "--session", session_id, "--specialist", "security")["result_id"]

    run_ok("finding", "create", "--session", session_id, "--result", result_id,
           "--specialist", "security", "--category", "vuln", "--severity", "high",
           "--title", "Issue one", "--detail", "Detail one")
    run_ok("finding", "create", "--session", session_id, "--result", result_id,
           "--specialist", "security", "--category", "vuln", "--severity", "low",
           "--title", "Issue two", "--detail", "Detail two")

    result = run_json("finding", "list", "--session", session_id)
    assert len(result) >= 2


def test_finding_list_filters_by_specialist():
    session_id = _make_session()
    sec_result = run_json("result", "create", "--session", session_id, "--specialist", "security")["result_id"]
    perf_result = run_json("result", "create", "--session", session_id, "--specialist", "performance")["result_id"]

    run_ok("finding", "create", "--session", session_id, "--result", sec_result,
           "--specialist", "security", "--category", "vuln", "--severity", "high",
           "--title", "Security issue", "--detail", "Details")
    run_ok("finding", "create", "--session", session_id, "--result", perf_result,
           "--specialist", "performance", "--category", "perf", "--severity", "low",
           "--title", "Perf issue", "--detail", "Details")

    result = run_json("finding", "list", "--session", session_id, "--specialist", "security")
    assert len(result) >= 1
    for row in result:
        assert row["specialist"] == "security"


def test_finding_list_filters_by_severity():
    session_id = _make_session()
    result_id = run_json("result", "create", "--session", session_id, "--specialist", "security")["result_id"]

    run_ok("finding", "create", "--session", session_id, "--result", result_id,
           "--specialist", "security", "--category", "vuln", "--severity", "critical",
           "--title", "Critical issue", "--detail", "Details")
    run_ok("finding", "create", "--session", session_id, "--result", result_id,
           "--specialist", "security", "--category", "vuln", "--severity", "low",
           "--title", "Low issue", "--detail", "Details")

    result = run_json("finding", "list", "--session", session_id, "--severity", "critical")
    assert len(result) >= 1
    for row in result:
        assert row["severity"] == "critical"


def test_finding_link_artifact_adds_to_linked_artifacts():
    session_id = _make_session()
    result_id = run_json("result", "create", "--session", session_id, "--specialist", "security")["result_id"]

    finding_id = run_json(
        "finding", "create",
        "--session", session_id, "--result", result_id, "--specialist", "security",
        "--category", "vuln", "--severity", "high", "--title", "Link test", "--detail", "Details",
    )["finding_id"]

    run_ok("finding", "link-artifact", "--finding", finding_id, "--artifact", "artifact-abc-123")

    result = run_json("finding", "get", "--finding", finding_id)
    assert len(result["linked_artifacts"]) == 1
    assert result["linked_artifacts"][0] == "artifact-abc-123"
