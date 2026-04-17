"""Contract tests for state resource."""
import pytest
from tp_helpers import run_arbitrator, run_ok, run_json, make_session


def test_state_append_creates_record_with_all_fields():
    session_id = make_session()

    result = run_json(
        "state", "append",
        "--session", session_id,
        "--changed-by", "orchestrator",
        "--state", "running",
        "--description", "Workflow started",
    )
    assert result["session_id"] == session_id
    assert result["changed_by"] == "orchestrator"
    assert result["state"] == "running"
    assert result["description"] == "Workflow started"
    assert result["id"]
    assert result["creation_date"]


def test_state_append_id_is_composite():
    session_id = make_session()

    result = run_json(
        "state", "append",
        "--session", session_id,
        "--changed-by", "orchestrator",
        "--state", "pending",
    )
    assert result["id"].startswith(f"{session_id}:state:")


def test_state_current_returns_latest_for_changed_by():
    session_id = make_session()

    run_ok("state", "append", "--session", session_id, "--changed-by", "orchestrator", "--state", "pending")
    run_ok("state", "append", "--session", session_id, "--changed-by", "orchestrator", "--state", "running")

    result = run_json("state", "current", "--session", session_id, "--changed-by", "orchestrator")
    assert result["state"] == "running"


def test_state_current_returns_latest_after_multiple_appends():
    session_id = make_session()

    run_ok("state", "append", "--session", session_id, "--changed-by", "worker", "--state", "pending")
    run_ok("state", "append", "--session", session_id, "--changed-by", "worker", "--state", "running")
    run_ok("state", "append", "--session", session_id, "--changed-by", "worker", "--state", "complete")

    result = run_json("state", "current", "--session", session_id, "--changed-by", "worker")
    assert result["state"] == "complete"


def test_state_list_returns_all_transitions_in_order():
    session_id = make_session()

    run_ok("state", "append", "--session", session_id, "--changed-by", "orchestrator", "--state", "pending")
    run_ok("state", "append", "--session", session_id, "--changed-by", "orchestrator", "--state", "running")
    run_ok("state", "append", "--session", session_id, "--changed-by", "orchestrator", "--state", "complete")

    result = run_json("state", "list", "--session", session_id)
    assert len(result) == 3
    assert result[0]["state"] == "pending"
    assert result[2]["state"] == "complete"


def test_state_list_returns_empty_for_new_session():
    session_id = make_session()

    result = run_json("state", "list", "--session", session_id)
    assert len(result) == 0


def test_state_append_fails_with_missing_required_flags():
    session_id = make_session()

    result = run_arbitrator("state", "append", "--session", session_id, "--changed-by", "orchestrator")
    assert result.returncode != 0
