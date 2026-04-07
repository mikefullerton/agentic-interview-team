"""Smoke tests for arbitrator.py and project_storage.py dispatchers.

Verifies that the thin wrapper scripts correctly delegate to
storage_provider.py and produce identical results.
"""

import json

from conftest import (
    ARBITRATOR, PROJECT_STORAGE, STORAGE_PROVIDER,
    run_json, run_ok, run_script,
)


# ---------------------------------------------------------------------------
# arbitrator.py delegation
# ---------------------------------------------------------------------------

class TestArbitratorDispatch:
    def test_creates_session_via_arbitrator(self):
        data = run_json(ARBITRATOR, [
            "session", "create",
            "--playbook", "smoke",
            "--team-lead", "tl",
            "--user", "u",
            "--machine", "m",
        ])
        assert "session_id" in data

    def test_session_readable_via_storage_provider(self):
        """Session created through arbitrator is readable through storage_provider."""
        data = run_json(ARBITRATOR, [
            "session", "create",
            "--playbook", "cross-read",
            "--team-lead", "tl",
            "--user", "u",
            "--machine", "m",
        ])
        got = run_json(STORAGE_PROVIDER, [
            "session", "get",
            "--session", data["session_id"],
        ])
        assert got["playbook"] == "cross-read"

    def test_message_via_arbitrator(self):
        sid = run_json(ARBITRATOR, [
            "session", "create",
            "--playbook", "smoke",
            "--team-lead", "tl",
            "--user", "u",
            "--machine", "m",
        ])["session_id"]

        msg = run_json(ARBITRATOR, [
            "message", "send",
            "--session", sid,
            "--type", "question",
            "--changed-by", "specialist",
            "--content", "Hello from arbitrator",
        ])
        assert msg["content"] == "Hello from arbitrator"

    def test_arbitrator_usage_on_missing_args(self):
        result = run_script(ARBITRATOR, [])
        assert result.returncode != 0
        assert "Usage" in result.stderr


# ---------------------------------------------------------------------------
# project_storage.py delegation
# ---------------------------------------------------------------------------

class TestProjectStorageDispatch:
    def test_creates_project_via_project_storage(self, project_path):
        project_path.mkdir(parents=True)
        data = run_json(PROJECT_STORAGE, [
            "project", "init",
            "--name", "Dispatch Test",
            "--description", "Test dispatch",
            "--path", str(project_path),
        ])
        assert data["name"] == "Dispatch Test"

    def test_project_readable_via_storage_provider(self, project_path):
        """Project created through project_storage is readable through storage_provider."""
        project_path.mkdir(parents=True)
        run_json(PROJECT_STORAGE, [
            "project", "init",
            "--name", "Cross Read",
            "--description", "Test cross-read",
            "--path", str(project_path),
        ])
        status = run_json(STORAGE_PROVIDER, [
            "project", "status",
            "--project", str(project_path),
        ])
        assert status["name"] == "Cross Read"

    def test_todo_via_project_storage(self, project_path):
        project_path.mkdir(parents=True)
        run_json(PROJECT_STORAGE, [
            "project", "init",
            "--name", "Todo Dispatch",
            "--description", "Test todo dispatch",
            "--path", str(project_path),
        ])
        created = run_json(PROJECT_STORAGE, [
            "todo", "create",
            "--project", str(project_path),
            "--title", "Dispatch todo",
            "--description", "Created via project_storage",
            "--priority", "medium",
            "--status", "open",
        ])
        assert "id" in created

    def test_project_storage_usage_on_missing_args(self):
        result = run_script(PROJECT_STORAGE, [])
        assert result.returncode != 0
        assert "Usage" in result.stderr
