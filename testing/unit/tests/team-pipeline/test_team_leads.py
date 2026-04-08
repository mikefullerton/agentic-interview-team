"""Tests for team-pipeline team-lead definitions."""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
TEAM_LEADS_DIR = REPO_ROOT / "plugins" / "team-pipeline" / "team-leads"

EXPECTED_LEADS = ["interview.md", "analysis.md"]

REQUIRED_SECTIONS = ["# ", "## Role", "## Persona", "## Phases", "## Interaction Style"]
REQUIRED_PERSONA_SUBS = ["### Archetype", "### Voice", "### Priorities"]


@pytest.mark.parametrize("lead_file", EXPECTED_LEADS)
def test_lead_file_exists(lead_file):
    assert (TEAM_LEADS_DIR / lead_file).is_file()


@pytest.mark.parametrize("lead_file", EXPECTED_LEADS)
def test_lead_has_required_sections(lead_file):
    content = (TEAM_LEADS_DIR / lead_file).read_text()
    for section in REQUIRED_SECTIONS:
        assert section in content, f"{lead_file} missing section: {section}"


@pytest.mark.parametrize("lead_file", EXPECTED_LEADS)
def test_lead_has_persona_subsections(lead_file):
    content = (TEAM_LEADS_DIR / lead_file).read_text()
    for sub in REQUIRED_PERSONA_SUBS:
        assert sub in content, f"{lead_file} missing persona sub-section: {sub}"


@pytest.mark.parametrize("lead_file", EXPECTED_LEADS)
def test_lead_title_ends_with_team_lead(lead_file):
    content = (TEAM_LEADS_DIR / lead_file).read_text()
    first_line = content.strip().split("\n")[0]
    assert first_line.startswith("# ")
    assert "Team-Lead" in first_line


@pytest.mark.parametrize("lead_file", EXPECTED_LEADS)
def test_lead_no_cookbook_references(lead_file):
    content = (TEAM_LEADS_DIR / lead_file).read_text().lower()
    assert "cookbook" not in content
