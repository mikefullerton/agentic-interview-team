"""Contract tests for cross-type filtering."""
import pytest
from project_storage_helpers import run_storage, run_ok, run_json, make_project


def test_todo_list_with_multiple_filters_status_and_priority(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("todo", "create", "--project", str(project_dir), "--title", "High open todo",
           "--description", "Should match", "--priority", "high", "--status", "open")
    run_ok("todo", "create", "--project", str(project_dir), "--title", "Low open todo",
           "--description", "Should not match", "--priority", "low", "--status", "open")
    run_ok("todo", "create", "--project", str(project_dir), "--title", "High done todo",
           "--description", "Should not match", "--priority", "high", "--status", "done")

    result = run_json("todo", "list", "--project", str(project_dir), "--status", "open", "--priority", "high")
    assert len(result) == 1
    assert result[0]["title"] == "High open todo"


def test_todo_list_returns_empty_when_no_matches(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("todo", "create", "--project", str(project_dir), "--title", "Some todo",
           "--description", "Exists but won't match", "--priority", "low", "--status", "open")

    result = run_json("todo", "list", "--project", str(project_dir), "--status", "done")
    assert len(result) == 0


def test_issue_list_returns_only_matching_severity(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("issue", "create", "--project", str(project_dir), "--title", "Critical bug",
           "--description", "App crashes on login", "--severity", "critical", "--status", "open")
    run_ok("issue", "create", "--project", str(project_dir), "--title", "Minor UI glitch",
           "--description", "Button misaligned", "--severity", "low", "--status", "open")
    run_ok("issue", "create", "--project", str(project_dir), "--title", "Another critical",
           "--description", "Data corruption possible", "--severity", "critical", "--status", "open")

    result = run_json("issue", "list", "--project", str(project_dir), "--severity", "critical")
    assert len(result) == 2


def test_milestone_list_returns_only_matching_status(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("milestone", "create", "--project", str(project_dir), "--name", "Alpha",
           "--description", "Alpha release", "--status", "completed")
    run_ok("milestone", "create", "--project", str(project_dir), "--name", "Beta",
           "--description", "Beta release", "--status", "planned")
    run_ok("milestone", "create", "--project", str(project_dir), "--name", "GA",
           "--description", "General availability", "--status", "planned")

    result = run_json("milestone", "list", "--project", str(project_dir), "--status", "planned")
    assert len(result) == 2
