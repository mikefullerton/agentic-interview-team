"""Contract tests for update and delete operations."""
import pytest
from project_storage_helpers import run_storage, run_ok, run_json, make_project


def test_todo_update_changes_status(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    item_id = run_json("todo", "create", "--project", str(project_dir),
                       "--title", "Write tests", "--description", "Add contract tests",
                       "--priority", "high", "--status", "open")["id"]

    run_ok("todo", "update", "--project", str(project_dir), "--id", item_id, "--status", "done")
    result = run_json("todo", "get", "--project", str(project_dir), "--id", item_id)
    assert result["status"] == "done"


def test_todo_update_changes_priority(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    item_id = run_json("todo", "create", "--project", str(project_dir),
                       "--title", "Refactor auth", "--description", "Clean up auth module",
                       "--priority", "low", "--status", "open")["id"]

    run_ok("todo", "update", "--project", str(project_dir), "--id", item_id, "--priority", "high")
    result = run_json("todo", "get", "--project", str(project_dir), "--id", item_id)
    assert result["priority"] == "high"


def test_milestone_update_changes_target_date(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    item_id = run_json("milestone", "create", "--project", str(project_dir),
                       "--name", "Beta Release", "--description", "Public beta launch",
                       "--status", "planned", "--target-date", "2024-06-01")["id"]

    run_ok("milestone", "update", "--project", str(project_dir), "--id", item_id, "--target-date", "2024-07-15")
    result = run_json("milestone", "get", "--project", str(project_dir), "--id", item_id)
    assert result["target_date"] == "2024-07-15"


def test_issue_update_changes_severity(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    item_id = run_json("issue", "create", "--project", str(project_dir),
                       "--title", "Login timeout", "--description", "Users get logged out too quickly",
                       "--severity", "low", "--status", "open")["id"]

    run_ok("issue", "update", "--project", str(project_dir), "--id", item_id, "--severity", "high")
    result = run_json("issue", "get", "--project", str(project_dir), "--id", item_id)
    assert result["severity"] == "high"


def test_concern_update_changes_status(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    item_id = run_json("concern", "create", "--project", str(project_dir),
                       "--title", "Performance at scale",
                       "--description", "May not handle 10k concurrent users",
                       "--raised-by", "alice", "--status", "open")["id"]

    run_ok("concern", "update", "--project", str(project_dir), "--id", item_id, "--status", "resolved")
    result = run_json("concern", "get", "--project", str(project_dir), "--id", item_id)
    assert result["status"] == "resolved"


def test_todo_delete_removes_item(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    item_id = run_json("todo", "create", "--project", str(project_dir),
                       "--title", "Todo to delete", "--description", "This will be deleted",
                       "--priority", "low", "--status", "open")["id"]

    run_ok("todo", "delete", "--project", str(project_dir), "--id", item_id)

    result = run_storage("todo", "get", "--project", str(project_dir), "--id", item_id)
    assert result.returncode != 0


def test_issue_delete_removes_item(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    item_id = run_json("issue", "create", "--project", str(project_dir),
                       "--title", "Issue to delete", "--description", "This will be deleted",
                       "--severity", "low", "--status", "open")["id"]

    run_ok("issue", "delete", "--project", str(project_dir), "--id", item_id)

    result = run_storage("issue", "get", "--project", str(project_dir), "--id", item_id)
    assert result.returncode != 0


def test_delete_nonexistent_item_fails(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_storage("todo", "delete", "--project", str(project_dir), "--id", "todo-9999")
    assert result.returncode != 0


def test_update_sets_modified_date(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    item_id = run_json("todo", "create", "--project", str(project_dir),
                       "--title", "Dated todo", "--description", "Check modified date",
                       "--priority", "low", "--status", "open")["id"]

    run_ok("todo", "update", "--project", str(project_dir), "--id", item_id, "--status", "in-progress")
    result = run_json("todo", "get", "--project", str(project_dir), "--id", item_id)
    assert result["modified"]
