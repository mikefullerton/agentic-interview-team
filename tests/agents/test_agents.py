"""
Agent file validation — verifies every .md file in agents/ has valid
frontmatter, required fields, and correct field values.
"""

import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2] / "plugins" / "dev-team"
AGENTS_DIR = PLUGIN_ROOT / "agents"

KNOWN_FIELDS = {"name", "description", "tools", "permissionMode", "maxTurns", "model"}
REQUIRED_FIELDS = {"name", "description"}
VALID_PERMISSION_MODES = {"plan", "full", "bypassPermissions"}

KEBAB_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_agent_files():
    """Return sorted list of (stem, path) for every .md file in agents/."""
    if not AGENTS_DIR.exists():
        return []
    return sorted(
        (p.stem, p)
        for p in AGENTS_DIR.glob("*.md")
    )


def parse_frontmatter(content):
    """
    Parse YAML frontmatter from a markdown file.

    Handles multi-line list values (tools field uses `  - item` lines).
    Returns (fields_dict, body_str) or (None, None) if no frontmatter found.

    fields_dict values:
      - scalar fields: stripped string
      - list fields (e.g. tools): Python list of strings
    """
    match = re.match(r"^---\n([\s\S]*?)\n---\n([\s\S]*)$", content)
    if not match:
        return None, None

    raw_block = match.group(1)
    body = match.group(2)
    fields = {}
    current_key = None

    for line in raw_block.split("\n"):
        # List item continuation
        if current_key is not None and re.match(r"^  - ", line):
            fields[current_key].append(line[4:].strip())
            continue

        colon_idx = line.find(":")
        if colon_idx == -1:
            current_key = None
            continue

        key = line[:colon_idx].strip()
        value = line[colon_idx + 1:].strip()
        current_key = key

        if value == "":
            # Expect a list to follow
            fields[key] = []
        else:
            fields[key] = value

    return fields, body


# ---------------------------------------------------------------------------
# Parametrize over all agent files
# ---------------------------------------------------------------------------

AGENT_FILES = get_agent_files()


@pytest.mark.parametrize("name,path", AGENT_FILES)
def test_has_valid_frontmatter(name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None, f"{name}: missing or malformed --- delimited frontmatter block"


@pytest.mark.parametrize("name,path", AGENT_FILES)
def test_has_required_fields(name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None, f"{name}: missing frontmatter"
    for field in REQUIRED_FIELDS:
        assert field in fields, f"{name}: missing required field '{field}'"


@pytest.mark.parametrize("name,path", AGENT_FILES)
def test_no_unknown_fields(name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None, f"{name}: missing frontmatter"
    unknown = set(fields.keys()) - KNOWN_FIELDS
    assert not unknown, (
        f"{name}: unknown frontmatter field(s): {sorted(unknown)}. "
        f"Known fields: {sorted(KNOWN_FIELDS)}"
    )


@pytest.mark.parametrize("name,path", AGENT_FILES)
def test_name_matches_filename(name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None, f"{name}: missing frontmatter"
    assert fields["name"] == name, (
        f"name field '{fields['name']}' does not match filename '{name}'"
    )


@pytest.mark.parametrize("name,path", AGENT_FILES)
def test_name_is_kebab_case(name, path):
    assert KEBAB_RE.match(name), (
        f"Filename '{name}' is not kebab-case (must match ^[a-z][a-z0-9]*(-[a-z0-9]+)*$)"
    )


@pytest.mark.parametrize("name,path", AGENT_FILES)
def test_description_is_non_empty(name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None, f"{name}: missing frontmatter"
    assert len(fields.get("description", "").strip()) > 0, (
        f"{name}: description field is empty"
    )


@pytest.mark.parametrize("name,path", AGENT_FILES)
def test_tools_is_list_when_present(name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None, f"{name}: missing frontmatter"
    if "tools" not in fields:
        return
    assert isinstance(fields["tools"], list), (
        f"{name}: 'tools' must be a YAML list (lines starting with '  - ')"
    )
    assert len(fields["tools"]) > 0, (
        f"{name}: 'tools' is present but empty"
    )


@pytest.mark.parametrize("name,path", AGENT_FILES)
def test_permission_mode_is_valid_when_present(name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None, f"{name}: missing frontmatter"
    if "permissionMode" not in fields:
        return
    mode = fields["permissionMode"]
    assert mode in VALID_PERMISSION_MODES, (
        f"{name}: permissionMode '{mode}' is not valid. "
        f"Must be one of: {sorted(VALID_PERMISSION_MODES)}"
    )


@pytest.mark.parametrize("name,path", AGENT_FILES)
def test_max_turns_is_positive_integer_when_present(name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None, f"{name}: missing frontmatter"
    if "maxTurns" not in fields:
        return
    raw = fields["maxTurns"]
    assert isinstance(raw, str) and raw.isdigit(), (
        f"{name}: maxTurns '{raw}' must be a positive integer"
    )
    assert int(raw) > 0, (
        f"{name}: maxTurns must be > 0, got {raw}"
    )


@pytest.mark.parametrize("name,path", AGENT_FILES)
def test_body_is_non_empty(name, path):
    content = path.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    assert fields is not None, f"{name}: missing frontmatter"
    assert body is not None and len(body.strip()) > 0, (
        f"{name}: body (content after frontmatter) is empty"
    )


# ---------------------------------------------------------------------------
# Directory-level checks
# ---------------------------------------------------------------------------

def test_agents_directory_exists():
    assert AGENTS_DIR.exists(), f"Agents directory not found: {AGENTS_DIR}"


def test_has_expected_number_of_agent_files():
    assert len(AGENT_FILES) == 20, (
        f"Expected 20 agent files, found {len(AGENT_FILES)}: "
        f"{[name for name, _ in AGENT_FILES]}"
    )
