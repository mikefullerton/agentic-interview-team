"""Contract tests for issue resource."""
import pytest
from project_storage_helpers import run_storage, run_ok, run_json, make_project


def test_issue_create_returns_id(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_json("issue", "create",
                      "--project", str(project_dir),
                      "--title", "Login broken",
                      "--description", "Users cannot log in",
                      "--severity", "high",
                      "--status", "open")
    assert result["id"]


def test_issue_get_returns_all_fields_including_description(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    created = run_json("issue", "create",
                       "--project", str(project_dir),
                       "--title", "Crash on startup",
                       "--description", "App crashes immediately on launch",
                       "--severity", "critical",
                       "--status", "open")
    item_id = created["id"]

    result = run_json("issue", "get", "--project", str(project_dir), "--id", item_id)
    assert result["title"] == "Crash on startup"
    assert result["status"] == "open"
    assert result["severity"] == "critical"
    assert result["description"]
    assert result["created"]


def test_issue_list_returns_issues(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("issue", "create", "--project", str(project_dir), "--title", "I1", "--description", "Issue one", "--severity", "low", "--status", "open")
    run_ok("issue", "create", "--project", str(project_dir), "--title", "I2", "--description", "Issue two", "--severity", "high", "--status", "open")

    result = run_json("issue", "list", "--project", str(project_dir))
    assert len(result) == 2


def test_issue_list_filters_by_status(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("issue", "create", "--project", str(project_dir), "--title", "I1", "--description", "Open issue", "--severity", "low", "--status", "open")
    run_ok("issue", "create", "--project", str(project_dir), "--title", "I2", "--description", "Closed issue", "--severity", "low", "--status", "closed")

    result = run_json("issue", "list", "--project", str(project_dir), "--status", "closed")
    assert len(result) == 1
    assert result[0]["status"] == "closed"


def test_issue_list_filters_by_severity(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("issue", "create", "--project", str(project_dir), "--title", "Low", "--description", "Minor problem", "--severity", "low", "--status", "open")
    run_ok("issue", "create", "--project", str(project_dir), "--title", "Critical", "--description", "Major problem", "--severity", "critical", "--status", "open")

    result = run_json("issue", "list", "--project", str(project_dir), "--severity", "critical")
    assert len(result) == 1
    assert result[0]["severity"] == "critical"


def test_issue_create_with_optional_source(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    created = run_json("issue", "create",
                       "--project", str(project_dir),
                       "--title", "Sourced issue",
                       "--description", "Came from monitoring alert",
                       "--severity", "medium",
                       "--status", "open",
                       "--source", "monitoring")
    item_id = created["id"]

    result = run_json("issue", "get", "--project", str(project_dir), "--id", item_id)
    assert result["source"] == "monitoring"


def test_issue_create_fails_with_missing_flags(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_storage("issue", "create",
                         "--project", str(project_dir),
                         "--title", "Incomplete",
                         "--severity", "high")
    assert result.returncode != 0
