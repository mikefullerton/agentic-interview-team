"""Contract tests for artifact resource."""
import pytest
from tp_helpers import run_arbitrator, run_ok, run_json, make_session


def test_artifact_create_returns_artifact_id():
    session_id = make_session()
    result = run_json(
        "artifact", "create",
        "--session", session_id,
        "--artifact", "https://example.com/artifact/abc123",
    )
    assert result["artifact_id"]


def test_artifact_create_with_message_and_description():
    session_id = make_session()
    result = run_json(
        "artifact", "create",
        "--session", session_id,
        "--artifact", "https://example.com/artifact/def456",
        "--message", "Initial build",
        "--description", "First pass at the output artifact",
    )
    assert result["artifact_id"]

    listing = run_json("artifact", "list", "--session", session_id)
    assert listing[0]["message"] == "Initial build"
    assert listing[0]["description"] == "First pass at the output artifact"


def test_artifact_list_returns_all_artifacts():
    session_id = make_session()
    run_ok("artifact", "create", "--session", session_id, "--artifact", "https://example.com/a1")
    run_ok("artifact", "create", "--session", session_id, "--artifact", "https://example.com/a2")
    run_ok("artifact", "create", "--session", session_id, "--artifact", "https://example.com/a3")

    result = run_json("artifact", "list", "--session", session_id)
    assert len(result) == 3


def test_artifact_link_state_adds_to_linked_states():
    session_id = make_session()
    artifact_id = run_json(
        "artifact", "create",
        "--session", session_id,
        "--artifact", "https://example.com/artifact/xyz",
    )["artifact_id"]

    state_output = run_json(
        "state", "append",
        "--session", session_id,
        "--state", "reviewing",
        "--changed-by", "orchestrator",
    )
    state_id = state_output["id"]

    result = run_json(
        "artifact", "link-state",
        "--artifact", artifact_id,
        "--state", state_id,
    )
    assert len(result["linked_states"]) == 1
    assert result["linked_states"][0] == state_id
