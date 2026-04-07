"""Contract tests for todo resource."""
import pytest
from project_storage_helpers import run_storage, run_ok, run_json, make_project


def test_todo_create_returns_id(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_json("todo", "create",
                      "--project", str(project_dir),
                      "--title", "Write tests",
                      "--description", "Cover all edge cases",
                      "--priority", "high",
                      "--status", "open")
    assert result["id"]


def test_todo_get_returns_all_fields_including_description(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    created = run_json("todo", "create",
                       "--project", str(project_dir),
                       "--title", "Fix bug",
                       "--description", "Detailed bug description",
                       "--priority", "medium",
                       "--status", "open")
    item_id = created["id"]

    result = run_json("todo", "get", "--project", str(project_dir), "--id", item_id)
    assert result["title"] == "Fix bug"
    assert result["status"] == "open"
    assert result["priority"] == "medium"
    assert result["description"]
    assert result["created"]


def test_todo_list_returns_todos(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("todo", "create", "--project", str(project_dir), "--title", "T1", "--description", "Task one", "--priority", "high", "--status", "open")
    run_ok("todo", "create", "--project", str(project_dir), "--title", "T2", "--description", "Task two", "--priority", "low", "--status", "open")

    result = run_json("todo", "list", "--project", str(project_dir))
    assert len(result) == 2


def test_todo_list_filters_by_status(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("todo", "create", "--project", str(project_dir), "--title", "T1", "--description", "Open task", "--priority", "high", "--status", "open")
    run_ok("todo", "create", "--project", str(project_dir), "--title", "T2", "--description", "Done task", "--priority", "low", "--status", "done")

    result = run_json("todo", "list", "--project", str(project_dir), "--status", "open")
    assert len(result) == 1
    assert result[0]["status"] == "open"


def test_todo_list_filters_by_priority(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("todo", "create", "--project", str(project_dir), "--title", "High P", "--description", "Urgent", "--priority", "high", "--status", "open")
    run_ok("todo", "create", "--project", str(project_dir), "--title", "Low P", "--description", "Not urgent", "--priority", "low", "--status", "open")

    result = run_json("todo", "list", "--project", str(project_dir), "--priority", "high")
    assert len(result) == 1
    assert result[0]["priority"] == "high"


def test_todo_create_with_optional_assignee_and_milestone(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    milestone_id = run_json("milestone", "create",
                             "--project", str(project_dir),
                             "--name", "Sprint 1",
                             "--description", "First sprint",
                             "--status", "pending")["id"]

    created = run_json("todo", "create",
                       "--project", str(project_dir),
                       "--title", "Assigned task",
                       "--description", "Task with assignee and milestone",
                       "--priority", "medium",
                       "--status", "open",
                       "--assignee", "alice",
                       "--milestone", milestone_id)
    item_id = created["id"]

    result = run_json("todo", "get", "--project", str(project_dir), "--id", item_id)
    assert result["assignee"] == "alice"
    assert result["milestone"] == milestone_id


def test_todo_create_fails_with_missing_flags(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_storage("todo", "create",
                         "--project", str(project_dir),
                         "--title", "Incomplete",
                         "--priority", "high")
    assert result.returncode != 0
