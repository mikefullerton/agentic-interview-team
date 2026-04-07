"""Contract tests for error handling."""
import pytest
from project_storage_helpers import run_storage, run_ok, run_json, make_project


def test_unknown_resource_fails():
    result = run_storage("nonexistent", "list", "--project", "/tmp")
    assert result.returncode != 0


def test_unknown_action_fails(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_storage("todo", "frobnicate", "--project", str(project_dir))
    assert result.returncode != 0


def test_get_nonexistent_item_fails(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_storage("todo", "get", "--project", str(project_dir), "--id", "todo-9999")
    assert result.returncode != 0


def test_create_on_nonexistent_project_fails(tmp_path):
    fake_dir = str(tmp_path / "no-such-project")
    result = run_storage("todo", "create",
                         "--project", fake_dir,
                         "--title", "Will fail",
                         "--description", "Project does not exist",
                         "--priority", "low",
                         "--status", "open")
    assert result.returncode != 0


def test_list_on_nonexistent_project_fails(tmp_path):
    fake_dir = str(tmp_path / "no-such-project")
    result = run_storage("todo", "list", "--project", fake_dir)
    assert result.returncode != 0
