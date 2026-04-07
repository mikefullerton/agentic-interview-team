"""Contract tests for concern resource."""
import pytest
from project_storage_helpers import run_storage, run_ok, run_json, make_project


def test_concern_create_returns_id(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_json("concern", "create",
                      "--project", str(project_dir),
                      "--title", "Scalability risk",
                      "--description", "System may not handle peak load",
                      "--raised-by", "alice",
                      "--status", "open")
    assert result["id"]


def test_concern_get_returns_all_fields_including_description(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    created = run_json("concern", "create",
                       "--project", str(project_dir),
                       "--title", "Data retention policy",
                       "--description", "No policy defined for user data retention",
                       "--raised-by", "bob",
                       "--status", "open")
    item_id = created["id"]

    result = run_json("concern", "get", "--project", str(project_dir), "--id", item_id)
    assert result["title"] == "Data retention policy"
    assert result["status"] == "open"
    assert result["raised_by"] == "bob"
    assert result["description"]
    assert result["created"]


def test_concern_list_returns_concerns(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("concern", "create", "--project", str(project_dir), "--title", "C1", "--description", "Concern one", "--raised-by", "alice", "--status", "open")
    run_ok("concern", "create", "--project", str(project_dir), "--title", "C2", "--description", "Concern two", "--raised-by", "bob", "--status", "open")

    result = run_json("concern", "list", "--project", str(project_dir))
    assert len(result) == 2


def test_concern_list_filters_by_status(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("concern", "create", "--project", str(project_dir), "--title", "C1", "--description", "Open concern", "--raised-by", "alice", "--status", "open")
    run_ok("concern", "create", "--project", str(project_dir), "--title", "C2", "--description", "Resolved concern", "--raised-by", "bob", "--status", "resolved")

    result = run_json("concern", "list", "--project", str(project_dir), "--status", "resolved")
    assert len(result) == 1
    assert result[0]["status"] == "resolved"


def test_concern_create_with_optional_related_to(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    created = run_json("concern", "create",
                       "--project", str(project_dir),
                       "--title", "Related concern",
                       "--description", "Links to an existing issue",
                       "--raised-by", "carol",
                       "--status", "open",
                       "--related-to", "issue-0001")
    item_id = created["id"]

    result = run_json("concern", "get", "--project", str(project_dir), "--id", item_id)
    assert result["related_to"] == "issue-0001"


def test_concern_create_fails_with_missing_flags(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_storage("concern", "create",
                         "--project", str(project_dir),
                         "--title", "Incomplete",
                         "--raised-by", "alice")
    assert result.returncode != 0
