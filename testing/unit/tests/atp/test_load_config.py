"""Tests for team-pipeline config loader."""
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
LOADER = str(REPO_ROOT / "skills" / "atp" / "scripts" / "load_config.py")


def write_config(tmp_path, data):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(data))
    return config_file


def test_loads_valid_config(tmp_path):
    cfg = write_config(tmp_path, {
        "team_name": "test-team",
        "user_name": "alice",
        "data_dir": "/tmp/data",
    })
    result = subprocess.run(
        ["python3", LOADER, "--config", str(cfg)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["team_name"] == "test-team"
    assert data["user_name"] == "alice"
    assert data["data_dir"] == "/tmp/data"


def test_passes_through_extra_fields(tmp_path):
    cfg = write_config(tmp_path, {
        "team_name": "test-team",
        "user_name": "bob",
        "data_dir": "/tmp/data",
        "custom_field": "custom_value",
        "sources": ["/path/to/docs"],
    })
    result = subprocess.run(
        ["python3", LOADER, "--config", str(cfg)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["custom_field"] == "custom_value"
    assert data["sources"] == ["/path/to/docs"]


def test_missing_required_field_fails(tmp_path):
    cfg = write_config(tmp_path, {
        "team_name": "test-team",
    })
    result = subprocess.run(
        ["python3", LOADER, "--config", str(cfg)],
        capture_output=True, text=True,
    )
    assert result.returncode == 1


def test_nonexistent_config_fails():
    result = subprocess.run(
        ["python3", LOADER, "--config", "/nonexistent/config.json"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
