"""
Tests for the dev-team skill: SKILL.md validation and workflow file checks.
"""

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parents[4]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "dev-team"
SKILL_DIR = PLUGIN_ROOT / "skills" / "dev-team"
SKILL_MD = SKILL_DIR / "SKILL.md"
WORKFLOWS_DIR = SKILL_DIR / "workflows"

EXPECTED_WORKFLOW_COUNT = 8

WORKFLOW_FILES = sorted(WORKFLOWS_DIR.glob("*.md")) if WORKFLOWS_DIR.exists() else []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) from a document that starts with ---.

    Parses line-by-line to handle values that contain colons without quoting,
    which would trip up yaml.safe_load.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    raw = text[3:end].strip()
    body = text[end + 3:].strip()

    fm: dict = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if key:
                fm[key] = value
    return fm, body


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Patterns that reference plugin-relative paths.
# Matches either:
#   ${CLAUDE_PLUGIN_ROOT}/agents/<path>
#   ${CLAUDE_PLUGIN_ROOT}/specialists/<path>
#   ${CLAUDE_PLUGIN_ROOT}/scripts/<path>
# or bare references like agents/<name>.md — must end with a file extension
# to avoid matching prose (e.g. "specialists/recipes.").
_PLUGIN_VAR = r"\$\{CLAUDE_(?:PLUGIN_ROOT|SKILL_DIR)\}/"
REF_PATTERN = re.compile(
    r"(?:"
    r"(?:" + _PLUGIN_VAR + r")(agents|specialists|scripts)/([\w.\-/]+)"
    r"|"
    r"(?<!\w)(agents|specialists|scripts)/([\w\-/]+\.(?:md|py|sh))"
    r")"
)


def extract_references(content: str) -> list[tuple[str, str]]:
    """Return list of (kind, relative_path) from content.

    The regex has two alternatives:
      group(1), group(2) — ${CLAUDE_PLUGIN_ROOT}/kind/path
      group(3), group(4) — bare kind/path.ext references
    """
    refs = []
    for m in REF_PATTERN.finditer(content):
        if m.group(1):
            kind, path = m.group(1), m.group(2)
        else:
            kind, path = m.group(3), m.group(4)
        path = path.rstrip(".,;)")
        refs.append((kind, path))
    return refs


# ---------------------------------------------------------------------------
# Directory-level tests
# ---------------------------------------------------------------------------

class TestDirectoryStructure:
    def test_skill_directory_exists(self):
        assert SKILL_DIR.is_dir(), f"Skill directory not found: {SKILL_DIR}"

    def test_skill_md_exists(self):
        assert SKILL_MD.is_file(), f"SKILL.md not found: {SKILL_MD}"

    def test_workflows_directory_exists(self):
        assert WORKFLOWS_DIR.is_dir(), f"Workflows directory not found: {WORKFLOWS_DIR}"

    def test_workflows_directory_has_8_files(self):
        count = len(WORKFLOW_FILES)
        assert count == EXPECTED_WORKFLOW_COUNT, (
            f"Expected {EXPECTED_WORKFLOW_COUNT} workflow files, found {count}: "
            f"{[f.name for f in WORKFLOW_FILES]}"
        )


# ---------------------------------------------------------------------------
# SKILL.md validation
# ---------------------------------------------------------------------------

class TestSkillMd:
    @pytest.fixture(scope="class")
    def skill_data(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        return fm, body

    def test_has_valid_frontmatter(self, skill_data):
        fm, _ = skill_data
        assert isinstance(fm, dict) and fm, "SKILL.md frontmatter is missing or invalid"

    def test_has_name_field(self, skill_data):
        fm, _ = skill_data
        assert "name" in fm, "SKILL.md frontmatter missing 'name' field"
        assert fm["name"] == "dev-team", (
            f"Expected name 'dev-team', got '{fm['name']}'"
        )

    def test_has_version_field(self, skill_data):
        fm, _ = skill_data
        assert "version" in fm, "SKILL.md frontmatter missing 'version' field"

    def test_version_is_semver(self, skill_data):
        fm, _ = skill_data
        version = str(fm.get("version", ""))
        assert SEMVER_RE.match(version), (
            f"Version '{version}' is not valid semver (N.N.N)"
        )

    def test_has_description_field(self, skill_data):
        fm, _ = skill_data
        assert "description" in fm, "SKILL.md frontmatter missing 'description' field"
        assert fm["description"], "SKILL.md 'description' field is empty"

    def test_version_appears_in_body(self, skill_data):
        fm, body = skill_data
        version = str(fm.get("version", ""))
        assert version in body, (
            f"Version '{version}' not found in SKILL.md body"
        )

    def test_routing_table_workflow_files_exist(self, skill_data):
        _, body = skill_data
        # Match rows like: | interview | workflows/interview.md |
        # or: | `interview` | `${CLAUDE_SKILL_DIR}/workflows/interview.md` |
        row_pattern = re.compile(
            r"\|\s*`?[\w-]+`?\s*\|\s*`?\S*workflows/([\w-]+\.md)`?\s*\|"
        )
        referenced = row_pattern.findall(body)
        assert referenced, "No workflow file references found in routing table"

        missing = []
        for filename in referenced:
            path = WORKFLOWS_DIR / filename
            if not path.is_file():
                missing.append(filename)

        assert not missing, (
            f"Workflow files referenced in routing table but not found: {missing}"
        )


# ---------------------------------------------------------------------------
# Workflow file validation (parametrized)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("workflow_file", WORKFLOW_FILES, ids=lambda f: f.name)
class TestWorkflowFiles:
    def test_file_is_non_empty(self, workflow_file):
        content = workflow_file.read_text(encoding="utf-8")
        assert content.strip(), f"{workflow_file.name} is empty"

    def test_agent_references_exist(self, workflow_file):
        content = workflow_file.read_text(encoding="utf-8")
        refs = [(k, p) for k, p in extract_references(content) if k == "agents"]
        missing = []
        for _, rel_path in refs:
            agent_file = PLUGIN_ROOT / "agents" / Path(rel_path).name
            if not agent_file.is_file():
                # Also try the path as-is relative to plugin root
                agent_file_full = PLUGIN_ROOT / "agents" / rel_path
                if not agent_file_full.is_file():
                    missing.append(rel_path)
        assert not missing, (
            f"{workflow_file.name} references missing agent files: {missing}"
        )

    def test_specialist_references_exist(self, workflow_file):
        content = workflow_file.read_text(encoding="utf-8")
        refs = [(k, p) for k, p in extract_references(content) if k == "specialists"]
        missing = []
        for _, rel_path in refs:
            # rel_path may be a bare domain name like "security" (no .md)
            candidate = PLUGIN_ROOT / "specialists" / rel_path
            if not candidate.exists():
                # Try appending .md
                candidate_md = PLUGIN_ROOT / "specialists" / (rel_path.rstrip(".") + ".md")
                if not candidate_md.is_file():
                    missing.append(rel_path)
        assert not missing, (
            f"{workflow_file.name} references missing specialist files: {missing}"
        )

    def test_script_references_exist(self, workflow_file):
        content = workflow_file.read_text(encoding="utf-8")
        refs = [(k, p) for k, p in extract_references(content) if k == "scripts"]
        missing = []
        for _, rel_path in refs:
            script_file = PLUGIN_ROOT / "scripts" / rel_path
            if not script_file.exists():
                missing.append(rel_path)
        assert not missing, (
            f"{workflow_file.name} references missing script files: {missing}"
        )
