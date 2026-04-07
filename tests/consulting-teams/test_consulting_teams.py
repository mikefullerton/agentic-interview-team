"""
Consulting-team file validation — verifies every file in consulting-teams/
has valid frontmatter and required sections.
"""

import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2] / "plugins" / "dev-team"
CONSULTING_TEAMS_DIR = PLUGIN_ROOT / "consulting-teams"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_all_consulting_team_files():
    """Return list of (category, name, path) tuples for every .md consulting-team file."""
    files = []
    if not CONSULTING_TEAMS_DIR.exists():
        return files
    for category_path in sorted(CONSULTING_TEAMS_DIR.iterdir()):
        if not category_path.is_dir():
            continue
        for file_path in sorted(category_path.glob("*.md")):
            files.append((category_path.name, file_path.stem, file_path))
    return files


def parse_frontmatter(content):
    """
    Parse YAML frontmatter from a markdown file, handling YAML lists for
    fields whose value is empty and followed by lines starting with '  - '.

    Returns (fields_dict, body_str) or (None, None) if no frontmatter found.
    Field values are str for scalar fields and list[str] for YAML list fields.
    """
    match = re.match(r"^---\n([\s\S]*?)\n---\n([\s\S]*)$", content)
    if not match:
        return None, None

    fields = {}
    lines = match.group(1).split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        colon_idx = line.find(":")
        if colon_idx == -1:
            i += 1
            continue
        key = line[:colon_idx].strip()
        value = line[colon_idx + 1:].strip()

        if value == "":
            # Collect YAML list items on subsequent lines
            list_items = []
            while i + 1 < len(lines) and lines[i + 1].startswith("  - "):
                i += 1
                list_items.append(lines[i][4:].strip())
            if list_items:
                fields[key] = list_items
                i += 1
                continue

        fields[key] = value
        i += 1

    return fields, match.group(2)


# ---------------------------------------------------------------------------
# Parametrize over all consulting-team files
# ---------------------------------------------------------------------------

CONSULTING_TEAM_FILES = get_all_consulting_team_files()


@pytest.mark.parametrize("category,name,path", CONSULTING_TEAM_FILES)
def test_has_valid_frontmatter(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None, "Missing or malformed frontmatter"


@pytest.mark.parametrize("category,name,path", CONSULTING_TEAM_FILES)
def test_has_required_frontmatter_fields(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None, "Missing or malformed frontmatter"
    assert "name" in fields
    assert "description" in fields
    assert "type" in fields
    assert "source" in fields
    assert "version" in fields


@pytest.mark.parametrize("category,name,path", CONSULTING_TEAM_FILES)
def test_type_is_consulting(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    assert fields["type"] == "consulting"


@pytest.mark.parametrize("category,name,path", CONSULTING_TEAM_FILES)
def test_name_matches_filename(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    assert fields["name"] == name


@pytest.mark.parametrize("category,name,path", CONSULTING_TEAM_FILES)
def test_name_is_kebab_case(category, name, path):
    assert re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", name), \
        f"Name '{name}' is not kebab-case"


@pytest.mark.parametrize("category,name,path", CONSULTING_TEAM_FILES)
def test_source_is_non_empty_list(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    source = fields["source"]
    assert isinstance(source, list), f"source must be a YAML list, got {type(source)}"
    assert len(source) > 0, "source list must not be empty"


@pytest.mark.parametrize("category,name,path", CONSULTING_TEAM_FILES)
def test_version_is_semver(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    assert re.match(r"^\d+\.\d+\.\d+$", fields["version"]), \
        f"version '{fields['version']}' is not semver"


@pytest.mark.parametrize("category,name,path", CONSULTING_TEAM_FILES)
def test_description_is_non_empty(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    description = fields["description"]
    assert isinstance(description, str)
    assert len(description) > 0


@pytest.mark.parametrize("category,name,path", CONSULTING_TEAM_FILES)
def test_has_consulting_focus_section(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    assert "## Consulting Focus" in body


@pytest.mark.parametrize("category,name,path", CONSULTING_TEAM_FILES)
def test_has_verify_section(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    assert "## Verify" in body


@pytest.mark.parametrize("category,name,path", CONSULTING_TEAM_FILES)
def test_consulting_focus_section_is_non_empty(category, name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None
    match = re.search(r"## Consulting Focus\n([\s\S]*?)(?=\n## |\n*$)", body)
    assert match is not None, "Consulting Focus section not found"
    assert len(match.group(1).strip()) > 0


@pytest.mark.parametrize("category,name,path", CONSULTING_TEAM_FILES)
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

def test_consulting_teams_directory_exists():
    assert CONSULTING_TEAMS_DIR.exists(), \
        f"consulting-teams directory not found at {CONSULTING_TEAMS_DIR}"


def test_has_at_least_one_consulting_team_file():
    assert len(CONSULTING_TEAM_FILES) > 0, \
        "No consulting-team files found"
