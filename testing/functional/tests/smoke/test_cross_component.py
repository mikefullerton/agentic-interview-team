"""Cross-component smoke tests.

Multi-step flows that exercise several components together,
verifying the system works end-to-end at the data layer.
"""

import json

from conftest import (
    ARBITRATOR, PROJECT_STORAGE, STORAGE_PROVIDER,
    run_json, run_ok, run_script,
)


class TestSessionLifecycle:
    """Full session lifecycle: create → messages → state → findings → result."""

    def test_full_session_flow(self):
        # 1. Create session
        session = run_json(ARBITRATOR, [
            "session", "create",
            "--playbook", "interview",
            "--team-lead", "team-lead",
            "--user", "tester",
            "--machine", "ci-host",
        ])
        sid = session["session_id"]

        # 2. Add a state transition
        run_json(STORAGE_PROVIDER, [
            "state", "append",
            "--session", sid,
            "--state", "in_progress",
            "--changed-by", "team-lead",
        ])

        # 3. Send messages back and forth
        run_json(ARBITRATOR, [
            "message", "send",
            "--session", sid,
            "--type", "question",
            "--changed-by", "security",
            "--content", "How do you handle auth?",
            "--specialist", "security",
        ])
        run_json(ARBITRATOR, [
            "message", "send",
            "--session", sid,
            "--type", "answer",
            "--changed-by", "user",
            "--content", "We use OAuth2 with PKCE",
        ])

        # 4. Create a result for the specialist
        result = run_json(STORAGE_PROVIDER, [
            "result", "create",
            "--session", sid,
            "--specialist", "security",
        ])
        assert "result_id" in result

        # 5. Record a finding against that result
        finding = run_json(STORAGE_PROVIDER, [
            "finding", "create",
            "--session", sid,
            "--result", result["result_id"],
            "--specialist", "security",
            "--category", "authentication",
            "--title", "OAuth2 with PKCE",
            "--detail", "Uses OAuth2 with PKCE flow",
            "--severity", "info",
        ])
        assert "id" in finding or "finding_id" in finding

        # 6. Verify messages are all there
        msgs = run_json(ARBITRATOR, ["message", "list", "--session", sid])
        assert len(msgs) == 2
        types = [m["type"] for m in msgs]
        assert "question" in types
        assert "answer" in types

    def test_multiple_specialists_in_session(self):
        sid = run_json(ARBITRATOR, [
            "session", "create",
            "--playbook", "interview",
            "--team-lead", "tl",
            "--user", "u",
            "--machine", "m",
        ])["session_id"]

        for specialist in ["security", "architecture", "testing-qa"]:
            run_json(ARBITRATOR, [
                "message", "send",
                "--session", sid,
                "--type", "question",
                "--changed-by", specialist,
                "--content", f"Question from {specialist}",
                "--specialist", specialist,
            ])

        msgs = run_json(ARBITRATOR, ["message", "list", "--session", sid])
        assert len(msgs) == 3


class TestProjectLifecycle:
    """Full project lifecycle: init → todos → issues → status check."""

    def test_full_project_flow(self, project_path):
        project_path.mkdir(parents=True)
        proj = str(project_path)

        # 1. Init project
        run_json(PROJECT_STORAGE, [
            "project", "init",
            "--name", "My App",
            "--description", "A test application",
            "--path", proj,
        ])

        # 2. Create todos
        t1 = run_json(STORAGE_PROVIDER, [
            "todo", "create",
            "--project", proj,
            "--title", "Set up auth",
            "--description", "Implement OAuth2",
            "--priority", "high",
            "--status", "open",
        ])
        t2 = run_json(STORAGE_PROVIDER, [
            "todo", "create",
            "--project", proj,
            "--title", "Add tests",
            "--description", "Unit and integration tests",
            "--priority", "medium",
            "--status", "open",
        ])

        # 3. Update a todo
        run_json(STORAGE_PROVIDER, [
            "todo", "update",
            "--project", proj,
            "--id", t1["id"],
            "--status", "in-progress",
        ])

        # 4. Check status
        status = run_json(STORAGE_PROVIDER, [
            "project", "status",
            "--project", proj,
        ])
        assert status["name"] == "My App"
        assert status["item_counts"]["todos"] == 2

        # 5. List todos filtered
        todos = run_json(STORAGE_PROVIDER, [
            "todo", "list",
            "--project", proj,
            "--status", "open",
        ])
        assert len(todos) == 1
        assert todos[0]["title"] == "Add tests"


class TestCrossComponentDataIntegrity:
    """Verify data written by one dispatcher is consistent when read by another."""

    def test_arbitrator_and_provider_share_session_state(self):
        # Create via arbitrator
        sid = run_json(ARBITRATOR, [
            "session", "create",
            "--playbook", "shared",
            "--team-lead", "tl",
            "--user", "u",
            "--machine", "m",
        ])["session_id"]

        # Write message via arbitrator
        run_json(ARBITRATOR, [
            "message", "send",
            "--session", sid,
            "--type", "note",
            "--changed-by", "system",
            "--content", "Cross-component check",
        ])

        # Read via storage-provider
        msgs = run_json(STORAGE_PROVIDER, [
            "message", "list",
            "--session", sid,
        ])
        assert len(msgs) == 1
        assert msgs[0]["content"] == "Cross-component check"

        # Read session via storage-provider
        sess = run_json(STORAGE_PROVIDER, [
            "session", "get",
            "--session", sid,
        ])
        assert sess["playbook"] == "shared"

    def test_project_storage_and_provider_share_project_data(self, project_path):
        project_path.mkdir(parents=True)
        proj = str(project_path)

        # Init via project_storage
        run_json(PROJECT_STORAGE, [
            "project", "init",
            "--name", "Shared",
            "--description", "Cross-read test",
            "--path", proj,
        ])

        # Create todo via project_storage
        run_json(PROJECT_STORAGE, [
            "todo", "create",
            "--project", proj,
            "--title", "Cross-component todo",
            "--description", "Test data sharing",
            "--priority", "high",
            "--status", "open",
        ])

        # Read todo list via storage-provider
        todos = run_json(STORAGE_PROVIDER, [
            "todo", "list",
            "--project", proj,
        ])
        assert len(todos) == 1
        assert todos[0]["title"] == "Cross-component todo"
