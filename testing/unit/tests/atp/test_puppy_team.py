"""Tests for name-a-puppy test team — validates against team-pipeline specs."""
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
PUPPY_DIR = REPO_ROOT / "plugins" / "name-a-puppy"
PARSER = str(REPO_ROOT / "skills" / "atp" / "scripts" / "run_specialty_teams.py")

SPECIALISTS = ["temperament.md", "breed.md", "lifestyle.md"]

EXPECTED_TEAMS = {
    "temperament": ["energy-level.md", "sociability.md"],
    "breed": ["size-traits.md", "name-traditions.md"],
    "lifestyle": ["living-space.md", "activity-level.md"],
}


@pytest.mark.parametrize("spec_file", SPECIALISTS)
def test_specialist_exists(spec_file):
    assert (PUPPY_DIR / "specialists" / spec_file).is_file()


@pytest.mark.parametrize("spec_file", SPECIALISTS)
def test_specialist_has_required_sections(spec_file):
    content = (PUPPY_DIR / "specialists" / spec_file).read_text()
    assert "# " in content
    assert "## Role" in content
    assert "## Sources" in content
    assert "## Manifest" in content


@pytest.mark.parametrize("category,teams", list(EXPECTED_TEAMS.items()))
def test_specialty_team_files_exist(category, teams):
    for team in teams:
        path = PUPPY_DIR / "specialty-teams" / category / team
        assert path.is_file(), f"Missing: {path}"


@pytest.mark.parametrize("category,teams", list(EXPECTED_TEAMS.items()))
def test_specialty_teams_have_frontmatter(category, teams):
    for team in teams:
        content = (PUPPY_DIR / "specialty-teams" / category / team).read_text()
        assert content.startswith("---")
        assert "name:" in content
        assert "version:" in content


@pytest.mark.parametrize("category,teams", list(EXPECTED_TEAMS.items()))
def test_specialty_teams_have_body_sections(category, teams):
    for team in teams:
        content = (PUPPY_DIR / "specialty-teams" / category / team).read_text()
        assert "## Worker Focus" in content
        assert "## Verify" in content


@pytest.mark.parametrize("spec_file", SPECIALISTS)
def test_manifest_parses_successfully(spec_file):
    spec_path = str(PUPPY_DIR / "specialists" / spec_file)
    result = subprocess.run(
        ["python3", PARSER, spec_path],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Parser failed for {spec_file}: {result.stderr}"
    data = json.loads(result.stdout)
    assert len(data["specialty_teams"]) > 0
