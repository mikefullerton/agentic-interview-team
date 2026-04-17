"""Tests for team-pipeline agent definitions."""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
AGENTS_DIR = REPO_ROOT / "skills" / "atp" / "agents"

EXPECTED_AGENTS = [
    "specialty-team-worker.md",
    "specialty-team-verifier.md",
    "consulting-team-worker.md",
    "consulting-team-verifier.md",
]


@pytest.mark.parametrize("agent_file", EXPECTED_AGENTS)
def test_agent_file_exists(agent_file):
    assert (AGENTS_DIR / agent_file).is_file()


@pytest.mark.parametrize("agent_file", EXPECTED_AGENTS)
def test_agent_has_frontmatter(agent_file):
    content = (AGENTS_DIR / agent_file).read_text()
    assert content.startswith("---")
    assert content.count("---") >= 2


@pytest.mark.parametrize("agent_file", EXPECTED_AGENTS)
def test_agent_has_name_field(agent_file):
    content = (AGENTS_DIR / agent_file).read_text()
    assert "name:" in content


@pytest.mark.parametrize("agent_file", EXPECTED_AGENTS)
def test_agent_no_cookbook_references(agent_file):
    content = (AGENTS_DIR / agent_file).read_text().lower()
    assert "cookbook" not in content, f"{agent_file} still references 'cookbook'"


def test_worker_has_four_modes():
    content = (AGENTS_DIR / "specialty-team-worker.md").read_text()
    assert "### Mode: interview" in content
    assert "### Mode: analysis" in content
    assert "### Mode: generation" in content
    assert "### Mode: review" in content


def test_no_extra_agents():
    agent_files = sorted(f.name for f in AGENTS_DIR.glob("*.md"))
    assert agent_files == sorted(EXPECTED_AGENTS)
