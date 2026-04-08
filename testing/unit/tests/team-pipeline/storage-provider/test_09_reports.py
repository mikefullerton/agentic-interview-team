"""Contract tests for report queries (progressive disclosure)."""
import pytest
from tp_helpers import run_arbitrator, run_ok, run_json, make_session


def _setup_populated_session():
    session_id = make_session(playbook="generate", team_lead="analysis")

    # State transitions
    run_ok("state", "append", "--session", session_id, "--changed-by", "team-lead:analysis", "--state", "running", "--description", "Starting")
    run_ok("state", "append", "--session", session_id, "--changed-by", "specialist:security", "--state", "running", "--description", "Analyzing")

    # Result + findings
    result_id = run_json("result", "create", "--session", session_id, "--specialist", "security")["result_id"]

    finding_id = run_json(
        "finding", "create",
        "--session", session_id, "--result", result_id, "--specialist", "security",
        "--category", "gap", "--severity", "critical", "--title", "No CSRF", "--detail", "Missing CSRF tokens",
    )["finding_id"]

    run_ok(
        "finding", "create",
        "--session", session_id, "--result", result_id, "--specialist", "security",
        "--category", "recommendation", "--severity", "minor", "--title", "Add rate limiting", "--detail", "API has no rate limits",
    )

    # Interpretation
    run_ok(
        "interpretation", "create",
        "--session", session_id, "--finding", finding_id, "--specialist", "security",
        "--interpretation", "Your forms are vulnerable to cross-site request forgery",
    )

    # Artifact linked to finding
    artifact_id = run_json(
        "artifact", "create",
        "--session", session_id, "--artifact", "guidelines/security/csrf.md",
        "--message", "CSRF guideline requires token validation",
    )["artifact_id"]
    run_ok("finding", "link-artifact", "--finding", finding_id, "--artifact", artifact_id)

    # Reference
    run_ok("session", "add-path", "--session", session_id, "--path", "guidelines/security/auth.md", "--type", "guideline")
    run_ok("reference", "create", "--result", result_id, "--path", "guidelines/security/auth.md", "--type", "guideline")

    # Message
    run_ok(
        "message", "send",
        "--session", session_id, "--type", "notification", "--changed-by", "team-lead:analysis",
        "--content", "Security analysis complete", "--specialist", "security", "--severity", "info", "--category", "result",
    )

    # Retry
    state_id = run_json(
        "state", "append",
        "--session", session_id, "--changed-by", "specialist:security", "--state", "failed", "--description", "Verifier rejected",
    )["id"]
    run_ok("retry", "create", "--session", session_id, "--state", state_id, "--reason", "Missing auth checks")

    return session_id, finding_id


def test_report_overview_returns_session_and_state_and_specialists():
    session_id, _ = _setup_populated_session()

    result = run_json("report", "overview", "--session", session_id)

    assert result["session"]["playbook"] == "generate"
    assert result["current_state"]["state"]

    specialists = result["specialists"]
    assert len(specialists) >= 1

    security = next(s for s in specialists if s["specialist"] == "security")
    assert security["findings_count"] == 2


def test_report_specialist_returns_result_and_findings_and_interpretations_and_references():
    session_id, _ = _setup_populated_session()

    result = run_json("report", "specialist", "--session", session_id, "--specialist", "security")

    assert result["result"]["specialist"] == "security"
    assert len(result["findings"]) == 2
    assert len(result["interpretations"]) == 1
    assert len(result["references"]) == 1


def test_report_finding_returns_detail_and_interpretation_and_linked_artifacts():
    _, finding_id = _setup_populated_session()

    result = run_json("report", "finding", "--finding", finding_id)

    assert result["finding"]["title"] == "No CSRF"
    assert result["finding"]["severity"] == "critical"
    assert result["interpretation"]["interpretation"]
    assert len(result["linked_artifacts"]) == 1


def test_report_trace_returns_states_and_retries_and_messages():
    session_id, _ = _setup_populated_session()

    result = run_json("report", "trace", "--session", session_id)

    assert len(result["states"]) >= 3
    assert len(result["retries"]) == 1
    assert len(result["messages"]) == 1


def test_report_specialist_fails_for_nonexistent_specialist():
    session_id, _ = _setup_populated_session()

    proc = run_arbitrator("report", "specialist", "--session", session_id, "--specialist", "nonexistent")
    assert proc.returncode != 0
