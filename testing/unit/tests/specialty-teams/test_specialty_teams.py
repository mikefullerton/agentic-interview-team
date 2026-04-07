"""
Specialty-team file validation — verifies every file in specialty-teams/
has valid frontmatter and required sections.
"""

import json
import re
import subprocess
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[4] / "plugins" / "dev-team"
TEAMS_DIR = PLUGIN_ROOT / "specialty-teams"
SPECIALISTS_DIR = PLUGIN_ROOT / "specialists"
RUN_SCRIPT = PLUGIN_ROOT / "scripts" / "run_specialty_teams.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_all_team_files():
    """Return list of (category, name, path) tuples for every .md team file."""
    files = []
    if not TEAMS_DIR.exists():
        return files
    for category_path in sorted(TEAMS_DIR.iterdir()):
        if not category_path.is_dir():
            continue
        for file_path in sorted(category_path.glob("*.md")):
            files.append((category_path.name, file_path.stem, file_path))
    return files


def parse_frontmatter(content):
    """
    Parse YAML frontmatter from a markdown file.

    Returns (fields_dict, body_str) or (None, None) if no frontmatter found.
    """
    match = re.match(r"^---\n([\s\S]*?)\n---\n([\s\S]*)$", content)
    if not match:
        return None, None
    fields = {}
    for line in match.group(1).split("\n"):
        colon_idx = line.find(":")
        if colon_idx == -1:
            continue
        key = line[:colon_idx].strip()
        value = line[colon_idx + 1:].strip()
        fields[key] = value
    return fields, match.group(2)


def run_script(specialist_filename):
    """Run run_specialty_teams.py for the given specialist file and return parsed JSON."""
    result = subprocess.run(
        ["python3", str(RUN_SCRIPT), str(SPECIALISTS_DIR / specialist_filename)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Parametrize over all team files
# ---------------------------------------------------------------------------

TEAM_FILES = get_all_team_files()


@pytest.mark.parametrize("category,name,path", TEAM_FILES)
def test_has_valid_frontmatter(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None, "Missing or malformed frontmatter"


@pytest.mark.parametrize("category,name,path", TEAM_FILES)
def test_has_required_frontmatter_fields(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None, "Missing or malformed frontmatter"
    assert "name" in fields
    assert "description" in fields
    assert "artifact" in fields
    assert "version" in fields


@pytest.mark.parametrize("category,name,path", TEAM_FILES)
def test_name_matches_filename(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    assert fields["name"] == name


@pytest.mark.parametrize("category,name,path", TEAM_FILES)
def test_name_is_kebab_case(category, name, path):
    assert re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", name), \
        f"Name '{name}' is not kebab-case"


@pytest.mark.parametrize("category,name,path", TEAM_FILES)
def test_artifact_is_non_empty_path(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    artifact = fields["artifact"]
    assert len(artifact) > 0
    assert re.search(r"\.(md|json)$|/$", artifact), \
        f"artifact '{artifact}' must end with .md, .json, or /"


@pytest.mark.parametrize("category,name,path", TEAM_FILES)
def test_version_is_semver(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    assert re.match(r"^\d+\.\d+\.\d+$", fields["version"]), \
        f"version '{fields['version']}' is not semver"


@pytest.mark.parametrize("category,name,path", TEAM_FILES)
def test_description_is_non_empty(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    assert len(fields["description"]) > 0


@pytest.mark.parametrize("category,name,path", TEAM_FILES)
def test_has_worker_focus_section(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    assert "## Worker Focus" in body


@pytest.mark.parametrize("category,name,path", TEAM_FILES)
def test_has_verify_section(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    assert "## Verify" in body


@pytest.mark.parametrize("category,name,path", TEAM_FILES)
def test_worker_focus_section_is_non_empty(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    match = re.search(r"## Worker Focus\n([\s\S]*?)(?=\n## |\n*$)", body)
    assert match is not None, "Worker Focus section not found"
    assert len(match.group(1).strip()) > 0


@pytest.mark.parametrize("category,name,path", TEAM_FILES)
def test_verify_section_is_non_empty(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    match = re.search(r"## Verify\n([\s\S]*?)(?=\n## |\n*$)", body)
    assert match is not None, "Verify section not found"
    assert len(match.group(1).strip()) > 0


# ---------------------------------------------------------------------------
# Directory structure tests
# ---------------------------------------------------------------------------

def test_has_at_least_one_category_directory():
    categories = [p for p in TEAMS_DIR.iterdir() if p.is_dir()]
    assert len(categories) > 0


def test_every_category_corresponds_to_a_specialist():
    category_to_specialist = {
        "project-management": "project-manager",
    }
    categories = [
        p.name
        for p in TEAMS_DIR.iterdir()
        if p.is_dir() and p.name != "_example"
    ]
    for category in categories:
        specialist_name = category_to_specialist.get(category, category)
        specialist_file = SPECIALISTS_DIR / f"{specialist_name}.md"
        assert specialist_file.exists(), (
            f"Category '{category}' has no matching specialist file "
            f"(looked for {specialist_name}.md)"
        )


def test_has_expected_number_of_team_files():
    assert len(TEAM_FILES) >= 200


# ---------------------------------------------------------------------------
# run_specialty_teams.py — basic output
# ---------------------------------------------------------------------------

def test_run_script_outputs_valid_json_for_accessibility():
    data = run_script("accessibility.md")
    assert isinstance(data["specialty_teams"], list)
    assert len(data["specialty_teams"]) == 2


def test_run_script_each_team_has_required_fields():
    data = run_script("accessibility.md")
    for team in data["specialty_teams"]:
        assert "name" in team
        assert "artifact" in team
        assert "worker_focus" in team
        assert "verify" in team


def test_run_script_outputs_correct_team_count_for_security():
    data = run_script("security.md")
    assert len(data["specialty_teams"]) == 15


def test_run_script_team_fields_match_file_content():
    data = run_script("security.md")
    auth_team = next(
        (t for t in data["specialty_teams"] if t["name"] == "authentication"),
        None,
    )
    assert auth_team is not None
    assert auth_team["artifact"] == "guidelines/security/authentication.md"
    assert len(auth_team["worker_focus"]) > 0
    assert len(auth_team["verify"]) > 0


# ---------------------------------------------------------------------------
# run_specialty_teams.py — consulting teams
# ---------------------------------------------------------------------------

def test_run_script_outputs_consulting_teams_for_example_specialist():
    data = run_script("_example.md")
    assert "consulting_teams" in data
    assert len(data["consulting_teams"]) == 1
    assert data["consulting_teams"][0]["name"] == "example-consulting-team"


def test_run_script_outputs_specialty_teams_for_example_specialist():
    data = run_script("_example.md")
    assert "specialty_teams" in data
    assert len(data["specialty_teams"]) == 1


def test_run_script_consulting_team_has_required_fields():
    data = run_script("_example.md")
    ct = data["consulting_teams"][0]
    assert "name" in ct
    assert "source" in ct
    assert "consulting_focus" in ct
    assert "verify" in ct
    assert ct["type"] == "consulting"


def test_run_script_specialist_without_consulting_teams_has_empty_array():
    data = run_script("accessibility.md")
    assert len(data["specialty_teams"]) == 2
    assert data["consulting_teams"] == []


# ---------------------------------------------------------------------------
# Specialist manifest integrity
# ---------------------------------------------------------------------------

SPECIALIST_FILES = sorted(SPECIALISTS_DIR.glob("*.md"))


@pytest.mark.parametrize("specialist_path", SPECIALIST_FILES)
def test_specialist_has_manifest_section(specialist_path):
    content = specialist_path.read_text(encoding="utf-8")
    assert "## Manifest" in content


@pytest.mark.parametrize("specialist_path", SPECIALIST_FILES)
def test_specialist_manifest_paths_resolve(specialist_path):
    content = specialist_path.read_text(encoding="utf-8")
    manifest_match = re.search(r"## Manifest\n([\s\S]*?)(?=\n## |\n*$)", content)
    assert manifest_match is not None, \
        f"{specialist_path.name} missing ## Manifest section"
    paths = [
        line[2:]
        for line in manifest_match.group(1).split("\n")
        if line.startswith("- ")
    ]
    assert len(paths) > 0
    for p in paths:
        full_path = PLUGIN_ROOT / p
        assert full_path.exists(), \
            f"{specialist_path.name} references missing file: {p}"


@pytest.mark.parametrize("specialist_path", SPECIALIST_FILES)
def test_specialist_has_no_embedded_specialty_teams_section(specialist_path):
    content = specialist_path.read_text(encoding="utf-8")
    assert "## Specialty Teams" not in content
