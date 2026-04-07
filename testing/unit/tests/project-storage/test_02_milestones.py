"""Contract tests for milestone resource."""
import pytest
from project_storage_helpers import run_storage, run_ok, run_json, make_project


def test_milestone_create_returns_id(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_json("milestone", "create",
                      "--project", str(project_dir),
                      "--name", "Launch v1",
                      "--description", "First release",
                      "--status", "pending")
    assert result["id"]


def test_milestone_get_returns_all_fields_including_description(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    created = run_json("milestone", "create",
                       "--project", str(project_dir),
                       "--name", "Phase One",
                       "--description", "Complete phase one work",
                       "--status", "pending")
    item_id = created["id"]

    result = run_json("milestone", "get", "--project", str(project_dir), "--id", item_id)
    assert result["name"] == "Phase One"
    assert result["status"] == "pending"
    assert result["description"]
    assert result["created"]


def test_milestone_list_returns_milestones(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("milestone", "create", "--project", str(project_dir), "--name", "M1", "--description", "Milestone one", "--status", "pending")
    run_ok("milestone", "create", "--project", str(project_dir), "--name", "M2", "--description", "Milestone two", "--status", "in-progress")

    result = run_json("milestone", "list", "--project", str(project_dir))
    assert len(result) == 2


def test_milestone_list_filters_by_status(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("milestone", "create", "--project", str(project_dir), "--name", "M1", "--description", "First", "--status", "pending")
    run_ok("milestone", "create", "--project", str(project_dir), "--name", "M2", "--description", "Second", "--status", "done")

    result = run_json("milestone", "list", "--project", str(project_dir), "--status", "done")
    assert len(result) == 1
    assert result[0]["status"] == "done"


def test_milestone_create_with_optional_target_date(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    created = run_json("milestone", "create",
                       "--project", str(project_dir),
                       "--name", "Dated Milestone",
                       "--description", "Has a target date",
                       "--status", "pending",
                       "--target-date", "2026-06-01")
    item_id = created["id"]

    result = run_json("milestone", "get", "--project", str(project_dir), "--id", item_id)
    assert result["target_date"] == "2026-06-01"


def test_milestone_create_fails_with_missing_flags(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_storage("milestone", "create",
                         "--project", str(project_dir),
                         "--name", "Incomplete",
                         "--status", "pending")
    assert result.returncode != 0
