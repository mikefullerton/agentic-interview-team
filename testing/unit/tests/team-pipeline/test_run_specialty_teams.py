"""Tests for team-pipeline manifest parser."""
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
PARSER = str(REPO_ROOT / "plugins" / "team-pipeline" / "scripts" / "run_specialty_teams.py")


def write_specialist(tmp_path, manifest_entries, consulting_entries=None):
    """Write a minimal specialist file and return its path."""
    spec_file = tmp_path / "specialists" / "test-spec.md"
    spec_file.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Test Specialist",
        "",
        "## Role",
        "Test role.",
        "",
        "## Persona",
        "(coming)",
        "",
        "## Sources",
        "- `sources/test/`",
        "",
        "## Manifest",
    ]
    for entry in manifest_entries:
        lines.append(f"- {entry}")

    if consulting_entries:
        lines.append("")
        lines.append("## Consulting Teams")
        for entry in consulting_entries:
            lines.append(f"- {entry}")

    spec_file.write_text("\n".join(lines) + "\n")
    return spec_file


def write_team_file(tmp_path, rel_path, name, source, focus, verify):
    """Write a specialty-team file at the given relative path."""
    team_file = tmp_path / rel_path
    team_file.parent.mkdir(parents=True, exist_ok=True)
    content = f"""---
name: {name}
description: Test team
artifact: {source}
version: 1.0.0
---

## Worker Focus
{focus}

## Verify
{verify}
"""
    team_file.write_text(content)
    return team_file


def write_consulting_file(tmp_path, rel_path, name, source_list, focus, verify):
    """Write a consulting-team file at the given relative path."""
    team_file = tmp_path / rel_path
    team_file.parent.mkdir(parents=True, exist_ok=True)
    source_yaml = "\n".join(f"  - {s}" for s in source_list)
    content = f"""---
name: {name}
description: Test consultant
type: consulting
source:
{source_yaml}
version: 1.0.0
---

## Consulting Focus
{focus}

## Verify
{verify}
"""
    team_file.write_text(content)
    return team_file


def test_parses_specialty_teams(tmp_path):
    write_team_file(
        tmp_path,
        "specialty-teams/test/energy.md",
        "energy", "sources/test/energy.md",
        "Evaluate energy levels", "Energy levels assessed",
    )
    spec = write_specialist(tmp_path, ["specialty-teams/test/energy.md"])

    result = subprocess.run(
        ["python3", PARSER, str(spec)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert len(data["specialty_teams"]) == 1
    assert data["specialty_teams"][0]["name"] == "energy"
    assert data["specialty_teams"][0]["worker_focus"] == "Evaluate energy levels"
    assert data["specialty_teams"][0]["verify"] == "Energy levels assessed"


def test_parses_consulting_teams(tmp_path):
    write_team_file(
        tmp_path,
        "specialty-teams/test/energy.md",
        "energy", "sources/test/energy.md",
        "Evaluate energy", "Energy assessed",
    )
    write_consulting_file(
        tmp_path,
        "consulting-teams/test/safety.md",
        "safety", ["docs/safety.md"],
        "Check safety concerns", "Safety verified",
    )
    spec = write_specialist(
        tmp_path,
        ["specialty-teams/test/energy.md"],
        consulting_entries=["consulting-teams/test/safety.md"],
    )

    result = subprocess.run(
        ["python3", PARSER, str(spec)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert len(data["consulting_teams"]) == 1
    assert data["consulting_teams"][0]["name"] == "safety"


def test_missing_specialist_file_fails():
    result = subprocess.run(
        ["python3", PARSER, "/nonexistent/file.md"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1


def test_empty_manifest_fails(tmp_path):
    spec_file = tmp_path / "specialists" / "empty.md"
    spec_file.parent.mkdir(parents=True, exist_ok=True)
    spec_file.write_text("# Empty\n\n## Role\nTest\n\n## Manifest\n")

    result = subprocess.run(
        ["python3", PARSER, str(spec_file)],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
