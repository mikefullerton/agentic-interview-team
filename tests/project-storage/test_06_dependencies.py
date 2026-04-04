"""Contract tests for dependency resource."""
import pytest
from project_storage_helpers import run_storage, run_ok, run_json, make_project


def test_dependency_create_returns_id(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_json("dependency", "create",
                      "--project", str(project_dir),
                      "--name", "Auth Service",
                      "--description", "External auth provider",
                      "--type", "external",
                      "--status", "active")
    assert result["id"]


def test_dependency_get_returns_all_fields_including_description(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    created = run_json("dependency", "create",
                       "--project", str(project_dir),
                       "--name", "Payment Gateway",
                       "--description", "Stripe integration for payments",
                       "--type", "external",
                       "--status", "active")
    item_id = created["id"]

    result = run_json("dependency", "get", "--project", str(project_dir), "--id", item_id)
    assert result["id"] == item_id
    assert result["name"] == "Payment Gateway"
    assert result["type"] == "external"
    assert result["status"] == "active"
    assert result["description"]
    assert result["created"]
    assert result["modified"]


def test_dependency_list_returns_dependencies(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("dependency", "create", "--project", str(project_dir), "--name", "Dep One", "--description", "First dependency", "--type", "internal", "--status", "active")
    run_ok("dependency", "create", "--project", str(project_dir), "--name", "Dep Two", "--description", "Second dependency", "--type", "external", "--status", "pending")

    result = run_json("dependency", "list", "--project", str(project_dir))
    assert len(result) == 2


def test_dependency_list_filters_by_status(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("dependency", "create", "--project", str(project_dir), "--name", "Active Dep", "--description", "An active dependency", "--type", "external", "--status", "active")
    run_ok("dependency", "create", "--project", str(project_dir), "--name", "Pending Dep", "--description", "A pending dependency", "--type", "external", "--status", "pending")

    result = run_json("dependency", "list", "--project", str(project_dir), "--status", "active")
    assert len(result) == 1
    assert result[0]["status"] == "active"


def test_dependency_list_filters_by_type(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("dependency", "create", "--project", str(project_dir), "--name", "Internal Dep", "--description", "An internal dependency", "--type", "internal", "--status", "active")
    run_ok("dependency", "create", "--project", str(project_dir), "--name", "External Dep", "--description", "An external dependency", "--type", "external", "--status", "active")

    result = run_json("dependency", "list", "--project", str(project_dir), "--type", "internal")
    assert len(result) == 1
    assert result[0]["type"] == "internal"


def test_dependency_create_fails_with_missing_flags(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_storage("dependency", "create",
                         "--project", str(project_dir),
                         "--name", "Incomplete",
                         "--description", "Missing required flags")
    assert result.returncode != 0
