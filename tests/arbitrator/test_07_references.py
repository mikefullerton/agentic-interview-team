"""Contract tests for reference resource."""
import pytest
from arbitrator_helpers import run_arbitrator, run_ok, run_json, make_session


def _make_result(session_id, specialist="security"):
    return run_json("result", "create", "--session", session_id, "--specialist", specialist)["result_id"]


def test_reference_create_returns_reference_id():
    session_id = make_session()
    result_id = _make_result(session_id)

    result = run_json(
        "reference", "create",
        "--result", result_id,
        "--path", "guidelines/security.md",
        "--type", "guideline",
    )
    assert result["reference_id"]


def test_reference_list_returns_references_for_a_result():
    session_id = make_session()
    result_id = _make_result(session_id, "ux")

    run_ok("reference", "create", "--result", result_id, "--path", "guidelines/ux.md", "--type", "guideline")
    run_ok("reference", "create", "--result", result_id, "--path", "principles/accessibility.md", "--type", "principle")

    result = run_json("reference", "list", "--result", result_id)
    assert len(result) == 2
    assert result[0]["type"] == "guideline"
    assert result[1]["type"] == "principle"


def test_reference_list_returns_empty_for_no_references():
    session_id = make_session()
    result_id = _make_result(session_id, "architecture")

    result = run_json("reference", "list", "--result", result_id)
    assert len(result) == 0
