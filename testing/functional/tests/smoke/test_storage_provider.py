"""Smoke tests for the unified storage-provider layer.

Verifies round-trip CRUD through storage_provider.py for both
arbitrator resources (session, message) and project-storage
resources (project, todo).
"""

import json

from conftest import STORAGE_PROVIDER, run_json, run_ok, run_script


# ---------------------------------------------------------------------------
# Session round-trip
# ---------------------------------------------------------------------------

class TestSessionRoundTrip:
    def test_create_and_get_session(self):
        data = run_json(STORAGE_PROVIDER, [
            "session", "create",
            "--playbook", "smoke",
            "--team-lead", "team-lead",
            "--user", "tester",
            "--machine", "ci",
        ])
        assert "session_id" in data

        got = run_json(STORAGE_PROVIDER, [
            "session", "get",
            "--session", data["session_id"],
        ])
        assert got["playbook"] == "smoke"
        assert got["team_lead"] == "team-lead"
        assert got["user"] == "tester"

    def test_list_sessions_returns_created(self):
        # Create two sessions
        s1 = run_json(STORAGE_PROVIDER, [
            "session", "create",
            "--playbook", "smoke",
            "--team-lead", "tl",
            "--user", "u",
            "--machine", "m",
        ])
        s2 = run_json(STORAGE_PROVIDER, [
            "session", "create",
            "--playbook", "other",
            "--team-lead", "tl",
            "--user", "u",
            "--machine", "m",
        ])

        all_sessions = run_json(STORAGE_PROVIDER, ["session", "list"])
        ids = [s["session_id"] for s in all_sessions]
        assert s1["session_id"] in ids
        assert s2["session_id"] in ids

    def test_list_sessions_filters_by_playbook(self):
        run_json(STORAGE_PROVIDER, [
            "session", "create",
            "--playbook", "alpha",
            "--team-lead", "tl",
            "--user", "u",
            "--machine", "m",
        ])
        run_json(STORAGE_PROVIDER, [
            "session", "create",
            "--playbook", "beta",
            "--team-lead", "tl",
            "--user", "u",
            "--machine", "m",
        ])

        filtered = run_json(STORAGE_PROVIDER, [
            "session", "list",
            "--playbook", "alpha",
        ])
        assert all(s["playbook"] == "alpha" for s in filtered)

    def test_add_path_to_session(self):
        s = run_json(STORAGE_PROVIDER, [
            "session", "create",
            "--playbook", "smoke",
            "--team-lead", "tl",
            "--user", "u",
            "--machine", "m",
        ])
        result = run_json(STORAGE_PROVIDER, [
            "session", "add-path",
            "--session", s["session_id"],
            "--path", "/tmp/workspace",
            "--type", "workspace",
        ])
        assert result["path"] == "/tmp/workspace"
        assert result["type"] == "workspace"


# ---------------------------------------------------------------------------
# Message round-trip
# ---------------------------------------------------------------------------

class TestMessageRoundTrip:
    def _make_session(self):
        return run_json(STORAGE_PROVIDER, [
            "session", "create",
            "--playbook", "smoke",
            "--team-lead", "tl",
            "--user", "u",
            "--machine", "m",
        ])["session_id"]

    def test_send_and_list_messages(self):
        sid = self._make_session()
        msg = run_json(STORAGE_PROVIDER, [
            "message", "send",
            "--session", sid,
            "--type", "question",
            "--changed-by", "specialist",
            "--content", "What framework?",
        ])
        assert msg["type"] == "question"
        assert msg["content"] == "What framework?"

        msgs = run_json(STORAGE_PROVIDER, ["message", "list", "--session", sid])
        assert len(msgs) == 1
        assert msgs[0]["content"] == "What framework?"

    def test_send_multiple_messages_sequential(self):
        sid = self._make_session()
        for i in range(3):
            run_ok(STORAGE_PROVIDER, [
                "message", "send",
                "--session", sid,
                "--type", "answer",
                "--changed-by", "user",
                "--content", f"Answer {i}",
            ])

        msgs = run_json(STORAGE_PROVIDER, ["message", "list", "--session", sid])
        assert len(msgs) == 3

    def test_message_filter_by_type(self):
        sid = self._make_session()
        run_ok(STORAGE_PROVIDER, [
            "message", "send",
            "--session", sid,
            "--type", "question",
            "--changed-by", "specialist",
            "--content", "Q1",
        ])
        run_ok(STORAGE_PROVIDER, [
            "message", "send",
            "--session", sid,
            "--type", "answer",
            "--changed-by", "user",
            "--content", "A1",
        ])

        questions = run_json(STORAGE_PROVIDER, [
            "message", "list",
            "--session", sid,
            "--type", "question",
        ])
        assert len(questions) == 1
        assert questions[0]["type"] == "question"


# ---------------------------------------------------------------------------
# Project round-trip
# ---------------------------------------------------------------------------

class TestProjectRoundTrip:
    def test_init_and_status(self, project_path):
        project_path.mkdir(parents=True)
        run_json(STORAGE_PROVIDER, [
            "project", "init",
            "--name", "Smoke Test",
            "--description", "A smoke test project",
            "--path", str(project_path),
        ])

        status = run_json(STORAGE_PROVIDER, [
            "project", "status",
            "--project", str(project_path),
        ])
        assert status["name"] == "Smoke Test"
        assert "item_counts" in status

    def test_link_and_unlink_cookbook(self, project_path):
        project_path.mkdir(parents=True)
        run_json(STORAGE_PROVIDER, [
            "project", "init",
            "--name", "Linktest",
            "--description", "Test linking",
            "--path", str(project_path),
        ])

        run_json(STORAGE_PROVIDER, [
            "project", "link-cookbook",
            "--project", str(project_path),
            "--path", "/repos/cookbook/recipes/auth",
        ])
        status = run_json(STORAGE_PROVIDER, [
            "project", "status",
            "--project", str(project_path),
        ])
        assert "/repos/cookbook/recipes/auth" in status["cookbook_projects"]

        run_json(STORAGE_PROVIDER, [
            "project", "unlink-cookbook",
            "--project", str(project_path),
            "--path", "/repos/cookbook/recipes/auth",
        ])
        status = run_json(STORAGE_PROVIDER, [
            "project", "status",
            "--project", str(project_path),
        ])
        assert "/repos/cookbook/recipes/auth" not in status["cookbook_projects"]


# ---------------------------------------------------------------------------
# Todo round-trip
# ---------------------------------------------------------------------------

class TestTodoRoundTrip:
    def _init_project(self, project_path):
        project_path.mkdir(parents=True)
        run_json(STORAGE_PROVIDER, [
            "project", "init",
            "--name", "Todo Smoke",
            "--description", "For todo tests",
            "--path", str(project_path),
        ])
        return str(project_path)

    def test_create_get_list_todo(self, project_path):
        proj = self._init_project(project_path)
        created = run_json(STORAGE_PROVIDER, [
            "todo", "create",
            "--project", proj,
            "--title", "Fix the widget",
            "--description", "Widget is broken",
            "--priority", "high",
            "--status", "open",
        ])
        assert "id" in created

        got = run_json(STORAGE_PROVIDER, [
            "todo", "get",
            "--project", proj,
            "--id", created["id"],
        ])
        assert got["title"] == "Fix the widget"
        assert got["priority"] == "high"

        todos = run_json(STORAGE_PROVIDER, [
            "todo", "list",
            "--project", proj,
        ])
        assert len(todos) == 1

    def test_update_todo(self, project_path):
        proj = self._init_project(project_path)
        created = run_json(STORAGE_PROVIDER, [
            "todo", "create",
            "--project", proj,
            "--title", "Update me",
            "--description", "Needs update",
            "--priority", "low",
            "--status", "open",
        ])

        run_json(STORAGE_PROVIDER, [
            "todo", "update",
            "--project", proj,
            "--id", created["id"],
            "--status", "done",
            "--priority", "high",
        ])

        got = run_json(STORAGE_PROVIDER, [
            "todo", "get",
            "--project", proj,
            "--id", created["id"],
        ])
        assert got["status"] == "done"
        assert got["priority"] == "high"

    def test_delete_todo(self, project_path):
        proj = self._init_project(project_path)
        created = run_json(STORAGE_PROVIDER, [
            "todo", "create",
            "--project", proj,
            "--title", "Delete me",
            "--description", "Temp",
            "--priority", "low",
            "--status", "open",
        ])

        run_json(STORAGE_PROVIDER, [
            "todo", "delete",
            "--project", proj,
            "--id", created["id"],
        ])

        todos = run_json(STORAGE_PROVIDER, [
            "todo", "list",
            "--project", proj,
        ])
        assert len(todos) == 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestStorageProviderErrors:
    def test_unknown_resource_exits_nonzero(self):
        result = run_script(STORAGE_PROVIDER, ["nonexistent", "list"])
        assert result.returncode != 0
        assert "Unknown resource" in result.stderr

    def test_missing_args_exits_nonzero(self):
        result = run_script(STORAGE_PROVIDER, ["session"])
        assert result.returncode != 0

    def test_no_args_shows_usage(self):
        result = run_script(STORAGE_PROVIDER, [])
        assert result.returncode != 0
        assert "Usage" in result.stderr
