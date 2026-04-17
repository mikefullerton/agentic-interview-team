"""Contract tests for retry resource."""
import pytest
from tp_helpers import run_arbitrator, run_ok, run_json, make_session


def _make_state(session_id):
    return run_json(
        "state", "append",
        "--session", session_id,
        "--state", "reviewing",
        "--changed-by", "orchestrator",
    )["id"]


def test_retry_create_returns_retry_id():
    session_id = make_session()
    state_id = _make_state(session_id)

    result = run_json(
        "retry", "create",
        "--session", session_id,
        "--state", state_id,
        "--reason", "Specialist output was incomplete",
    )
    assert result["retry_id"]


def test_retry_create_stores_reason_and_state_link():
    session_id = make_session()
    state_id = _make_state(session_id)

    run_ok(
        "retry", "create",
        "--session", session_id,
        "--state", state_id,
        "--reason", "Validation threshold not met",
    )

    result = run_json("retry", "list", "--session", session_id)
    assert result[0]["reason"] == "Validation threshold not met"
    assert result[0]["session_state_id"] == state_id
    assert result[0]["session_id"] == session_id


def test_retry_list_returns_all_retries():
    session_id = make_session()
    state_id = _make_state(session_id)

    run_ok("retry", "create", "--session", session_id, "--state", state_id, "--reason", "First retry")
    run_ok("retry", "create", "--session", session_id, "--state", state_id, "--reason", "Second retry")

    result = run_json("retry", "list", "--session", session_id)
    assert len(result) == 2
