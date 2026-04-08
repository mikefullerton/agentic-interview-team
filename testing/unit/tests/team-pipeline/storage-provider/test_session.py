"""Contract tests for team-pipeline session resource."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from tp_helpers import run_arbitrator, run_ok, run_json, make_session


def test_session_create_returns_session_id():
    data = run_json(
        "session", "create",
        "--playbook", "interview",
        "--team-lead", "interview",
        "--user", "testuser",
        "--machine", "testhost",
    )
    assert data["session_id"]


def test_session_get_returns_all_fields():
    data = run_json(
        "session", "create",
        "--playbook", "test-workflow",
        "--team-lead", "analysis",
        "--user", "alice",
        "--machine", "devbox",
    )
    session_id = data["session_id"]

    result = run_json("session", "get", "--session", session_id)
    assert result["playbook"] == "test-workflow"
    assert result["team_lead"] == "analysis"
    assert result["user"] == "alice"
    assert result["machine"] == "devbox"
    assert result["creation_date"]


def test_session_list_filters_by_playbook():
    run_ok("session", "create", "--playbook", "lint", "--team-lead", "audit", "--user", "bob", "--machine", "ci")
    run_ok("session", "create", "--playbook", "lint", "--team-lead", "audit", "--user", "bob", "--machine", "ci")
    run_ok("session", "create", "--playbook", "interview", "--team-lead", "interview", "--user", "bob", "--machine", "ci")

    result = run_json("session", "list", "--playbook", "lint")
    assert len(result) >= 2


def test_session_list_returns_empty_for_no_matches():
    result = run_json("session", "list", "--playbook", "nonexistent")
    assert len(result) == 0


def test_session_add_path_stores_path():
    session_id = make_session()

    result = run_json(
        "session", "add-path",
        "--session", session_id,
        "--path", "/tmp/test-repo",
        "--type", "repo",
    )
    assert result["type"] == "repo"
    assert result["path"] == "/tmp/test-repo"


def test_session_create_missing_flags_fails():
    result = run_arbitrator("session", "create", "--playbook", "test")
    assert result.returncode == 1


def test_session_get_nonexistent_fails():
    result = run_arbitrator("session", "get", "--session", "nonexistent-id")
    assert result.returncode == 1
