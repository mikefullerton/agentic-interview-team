"""Contract tests for project resource."""
import pytest
from pathlib import Path
from project_storage_helpers import run_storage, run_ok, run_json, make_project


def test_project_init_creates_manifest(tmp_path):
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    result = run_json("project", "init", "--name", "my-project", "--description", "Test", "--path", str(project_dir))
    assert result["name"] == "my-project"
    assert (project_dir / ".dev-team-project" / "manifest.json").exists()


def test_project_init_creates_subdirectories(tmp_path):
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    run_ok("project", "init", "--name", "test", "--description", "Test", "--path", str(project_dir))
    for subdir in ("schedule", "todos", "issues", "concerns", "dependencies", "decisions"):
        assert (project_dir / ".dev-team-project" / subdir).is_dir(), f"missing subdir: {subdir}"


def test_project_init_fails_on_duplicate(tmp_path):
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    run_ok("project", "init", "--name", "test", "--description", "Test", "--path", str(project_dir))
    result = run_storage("project", "init", "--name", "test", "--description", "Test", "--path", str(project_dir))
    assert result.returncode != 0


def test_project_status_returns_manifest_and_counts(tmp_path):
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_json("project", "status", "--project", str(project_dir))
    assert result["name"] == "test-project"
    assert str(result["item_counts"]["todos"]) == "0"
    assert str(result["item_counts"]["issues"]) == "0"


def test_project_link_cookbook_adds_paths(tmp_path):
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("project", "link-cookbook", "--project", str(project_dir), "--path", "/tmp/cookbook-a")
    run_ok("project", "link-cookbook", "--project", str(project_dir), "--path", "/tmp/cookbook-b")

    result = run_json("project", "status", "--project", str(project_dir))
    assert len(result["cookbook_projects"]) == 2


def test_project_link_cookbook_deduplicates(tmp_path):
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("project", "link-cookbook", "--project", str(project_dir), "--path", "/tmp/cookbook-a")
    run_ok("project", "link-cookbook", "--project", str(project_dir), "--path", "/tmp/cookbook-a")

    result = run_json("project", "status", "--project", str(project_dir))
    assert len(result["cookbook_projects"]) == 1


def test_project_unlink_cookbook_removes_path(tmp_path):
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("project", "link-cookbook", "--project", str(project_dir), "--path", "/tmp/cookbook-a")
    run_ok("project", "link-cookbook", "--project", str(project_dir), "--path", "/tmp/cookbook-b")
    run_ok("project", "unlink-cookbook", "--project", str(project_dir), "--path", "/tmp/cookbook-a")

    result = run_json("project", "status", "--project", str(project_dir))
    assert len(result["cookbook_projects"]) == 1
    assert result["cookbook_projects"][0] == "/tmp/cookbook-b"


def test_project_init_fails_with_missing_flags(tmp_path):
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    result = run_storage("project", "init", "--name", "test", "--path", str(project_dir))
    assert result.returncode != 0


def test_project_status_fails_for_nonexistent(tmp_path):
    result = run_storage("project", "status", "--project", str(tmp_path / "no-such-project"))
    assert result.returncode != 0
