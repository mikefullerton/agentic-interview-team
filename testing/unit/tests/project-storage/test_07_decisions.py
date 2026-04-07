"""Contract tests for decision resource."""
import pytest
from project_storage_helpers import run_storage, run_ok, run_json, make_project


def test_decision_create_returns_id(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_json("decision", "create",
                      "--project", str(project_dir),
                      "--title", "Use PostgreSQL",
                      "--description", "We will use PostgreSQL as the primary database",
                      "--rationale", "Strong ACID compliance and JSON support",
                      "--made-by", "architecture-team")
    assert result["id"]


def test_decision_get_returns_all_fields_including_description(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    created = run_json("decision", "create",
                       "--project", str(project_dir),
                       "--title", "Use TypeScript",
                       "--description", "Adopt TypeScript across the codebase",
                       "--rationale", "Type safety reduces runtime errors",
                       "--made-by", "tech-lead")
    item_id = created["id"]

    result = run_json("decision", "get", "--project", str(project_dir), "--id", item_id)
    assert result["id"] == item_id
    assert result["title"] == "Use TypeScript"
    assert result["rationale"] == "Type safety reduces runtime errors"
    assert result["made_by"] == "tech-lead"
    assert result["description"]
    assert result["date"]
    assert result["created"]
    assert result["modified"]


def test_decision_create_with_optional_alternatives_and_date(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    created = run_json("decision", "create",
                       "--project", str(project_dir),
                       "--title", "Choose Deployment Platform",
                       "--description", "Selected AWS over GCP and Azure",
                       "--rationale", "Existing team expertise and cost structure",
                       "--made-by", "cto",
                       "--alternatives", "GCP, Azure",
                       "--date", "2024-01-15")
    item_id = created["id"]

    result = run_json("decision", "get", "--project", str(project_dir), "--id", item_id)
    assert result["alternatives"] == "GCP, Azure"
    assert result["date"] == "2024-01-15"


def test_decision_list_returns_all_decisions(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    run_ok("decision", "create", "--project", str(project_dir), "--title", "Decision Alpha",
           "--description", "First decision", "--rationale", "Because alpha", "--made-by", "team")
    run_ok("decision", "create", "--project", str(project_dir), "--title", "Decision Beta",
           "--description", "Second decision", "--rationale", "Because beta", "--made-by", "team")

    result = run_json("decision", "list", "--project", str(project_dir))
    assert len(result) == 2


def test_decision_create_fails_with_missing_flags(tmp_path):
    project_dir = tmp_path / "p"
    project_dir.mkdir()
    make_project(project_dir)
    result = run_storage("decision", "create",
                         "--project", str(project_dir),
                         "--title", "Incomplete Decision",
                         "--description", "Missing required flags")
    assert result.returncode != 0
