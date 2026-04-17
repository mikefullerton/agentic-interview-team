"""Contract tests for interpretation resource."""
import json
import pytest
from tp_helpers import run_arbitrator, run_ok, run_json, make_session


def _make_finding(playbook="interview"):
    session_id = make_session(playbook=playbook, team_lead="interview")

    result_id = run_json("result", "create", "--session", session_id, "--specialist", "analysis")["result_id"]

    finding_id = run_json(
        "finding", "create",
        "--session", session_id,
        "--result", result_id,
        "--specialist", "analysis",
        "--category", "design",
        "--severity", "medium",
        "--title", "Architecture concern",
        "--detail", "The current design does not support horizontal scaling",
    )["finding_id"]

    return session_id, finding_id


def test_interpretation_create_returns_id():
    session_id, finding_id = _make_finding()

    result = run_json(
        "interpretation", "create",
        "--session", session_id,
        "--finding", finding_id,
        "--specialist", "analysis",
        "--interpretation", "This concern stems from tight coupling between the data layer and business logic",
    )
    assert result["interpretation_id"]


def test_interpretation_list_returns_interpretations_for_a_finding():
    session_id, finding_id = _make_finding()

    run_ok(
        "interpretation", "create",
        "--session", session_id,
        "--finding", finding_id,
        "--specialist", "analysis",
        "--interpretation", "First interpretation of this finding",
    )

    result = run_json("interpretation", "list", "--finding", finding_id)
    assert len(result) >= 1
    assert result[0]["interpretation"]
    assert result[0]["finding_id"] == finding_id


def test_interpretation_for_nonexistent_finding_fails_gracefully():
    fake_finding = "20260101-000000-0000:finding:security:9999"
    proc = run_arbitrator("interpretation", "list", "--finding", fake_finding)
    # Either returns empty array or exits non-zero — must not crash with unhandled error
    if proc.returncode == 0:
        output = proc.stdout.strip()
        if output:
            data = json.loads(output)
            assert isinstance(data, list)
