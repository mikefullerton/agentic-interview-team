"""
Tests for specialist definition files and assign_specialists.py script.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
PLUGIN_ROOT = REPO_ROOT / "plugins" / "dev-team"
SPECIALISTS_DIR = PLUGIN_ROOT / "specialists"
ASSIGN_SCRIPT = PLUGIN_ROOT / "scripts" / "assign_specialists.py"

EXPECTED_SPECIALIST_COUNT = 21


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_specialist_files():
    """Return all .md files in the specialists directory."""
    return sorted(SPECIALISTS_DIR.glob("*.md"))


def parse_sections(md_text: str) -> dict:
    """
    Split a markdown file into sections keyed by their ## heading.
    Returns a dict: { "Role": "<body text>", "Manifest": "<body text>", ... }
    The body text is everything between that heading and the next ## heading.
    """
    sections = {}
    current = None
    body_lines = []
    for line in md_text.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(body_lines).strip()
            current = line[3:].strip()
            body_lines = []
        else:
            if current is not None:
                body_lines.append(line)
    if current is not None:
        sections[current] = "\n".join(body_lines).strip()
    return sections


# ---------------------------------------------------------------------------
# Directory-level tests
# ---------------------------------------------------------------------------

class TestSpecialistsDirectory:
    def test_directory_exists(self):
        assert SPECIALISTS_DIR.is_dir(), f"Specialists directory not found: {SPECIALISTS_DIR}"

    def test_expected_file_count(self):
        files = get_specialist_files()
        assert len(files) == EXPECTED_SPECIALIST_COUNT, (
            f"Expected {EXPECTED_SPECIALIST_COUNT} specialist files, found {len(files)}:\n"
            + "\n".join(f.name for f in files)
        )


# ---------------------------------------------------------------------------
# Per-specialist parametrized tests
# ---------------------------------------------------------------------------

@pytest.fixture(params=get_specialist_files(), ids=lambda p: p.stem)
def specialist_file(request):
    return request.param


@pytest.fixture()
def specialist_sections(specialist_file):
    text = specialist_file.read_text(encoding="utf-8")
    return parse_sections(text)


class TestSpecialistFormat:
    def test_has_role_section(self, specialist_sections):
        assert "Role" in specialist_sections, "Missing ## Role section"
        assert specialist_sections["Role"].strip(), "## Role section is empty"

    def test_has_cookbook_sources_section(self, specialist_sections):
        assert "Cookbook Sources" in specialist_sections, "Missing ## Cookbook Sources section"
        body = specialist_sections["Cookbook Sources"]
        list_items = [ln for ln in body.splitlines() if ln.strip().startswith("- ")]
        assert len(list_items) >= 1, "## Cookbook Sources has no list items"

    def test_has_manifest_section(self, specialist_sections):
        assert "Manifest" in specialist_sections, "Missing ## Manifest section"
        body = specialist_sections["Manifest"]
        list_items = [ln for ln in body.splitlines() if ln.strip().startswith("- ")]
        assert len(list_items) >= 1, "## Manifest has no list items"

    def test_manifest_paths_exist(self, specialist_sections):
        body = specialist_sections.get("Manifest", "")
        missing = []
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- "):
                continue
            path_str = stripped[2:].strip()
            resolved = PLUGIN_ROOT / path_str
            if not resolved.exists():
                missing.append(path_str)
        assert not missing, (
            "Manifest paths that do not exist:\n" + "\n".join(f"  {p}" for p in missing)
        )

    def test_has_exploratory_prompts_section(self, specialist_sections):
        assert "Exploratory Prompts" in specialist_sections, "Missing ## Exploratory Prompts section"
        body = specialist_sections["Exploratory Prompts"]
        numbered_items = [ln for ln in body.splitlines() if ln.strip() and ln.strip()[0].isdigit()]
        assert len(numbered_items) >= 1, "## Exploratory Prompts has no numbered items"

    def test_consulting_teams_paths_exist(self, specialist_sections):
        """If ## Consulting Teams section is present, all paths must resolve."""
        if "Consulting Teams" not in specialist_sections:
            pytest.skip("No ## Consulting Teams section in this file")
        body = specialist_sections["Consulting Teams"]
        missing = []
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- "):
                continue
            path_str = stripped[2:].strip()
            resolved = PLUGIN_ROOT / path_str
            if not resolved.exists():
                missing.append(path_str)
        assert not missing, (
            "Consulting Teams paths that do not exist:\n"
            + "\n".join(f"  {p}" for p in missing)
        )

    def test_no_deprecated_specialty_teams_section(self, specialist_file):
        text = specialist_file.read_text(encoding="utf-8")
        # Check raw text for any ## Specialty Teams heading
        for line in text.splitlines():
            if line.strip().startswith("## ") and "Specialty Teams" in line:
                pytest.fail(
                    f"Deprecated '## Specialty Teams' section found in {specialist_file.name}. "
                    "Use '## Manifest' instead."
                )


# ---------------------------------------------------------------------------
# assign_specialists.py tests
# ---------------------------------------------------------------------------

def run_assign(recipe_path, platforms=None, tier_order=False, env=None):
    """Run assign_specialists.py and return (returncode, stdout, stderr)."""
    cmd = [sys.executable, str(ASSIGN_SCRIPT), str(recipe_path)]
    if platforms:
        cmd += ["--platforms", json.dumps(platforms)]
    if tier_order:
        cmd += ["--tier-order"]

    base_env = os.environ.copy()
    base_env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    if env:
        base_env.update(env)

    result = subprocess.run(cmd, capture_output=True, text=True, env=base_env)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def make_recipe(tmp_path, content: str, filename: str = "recipe.md") -> Path:
    """Write a temporary recipe file and return its path."""
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return p


class TestAssignSpecialists:
    def test_keyword_auth_triggers_security(self, tmp_path):
        """Recipe containing 'auth' should include the security specialist."""
        recipe = make_recipe(tmp_path, "This recipe handles auth via OAuth tokens.")
        rc, out, _ = run_assign(recipe)
        assert rc == 0
        specialists = out.splitlines()
        assert "security" in specialists

    def test_keyword_database_triggers_data_persistence(self, tmp_path):
        """Recipe containing 'database' should include data-persistence specialist."""
        recipe = make_recipe(tmp_path, "Store user records in a database with caching.")
        rc, out, _ = run_assign(recipe)
        assert rc == 0
        specialists = out.splitlines()
        assert "data-persistence" in specialists

    def test_keyword_api_triggers_networking(self, tmp_path):
        """Recipe containing 'API' should include networking-api specialist."""
        recipe = make_recipe(tmp_path, "Expose a REST API with HTTP endpoints.")
        rc, out, _ = run_assign(recipe)
        assert rc == 0
        specialists = out.splitlines()
        assert "networking-api" in specialists

    def test_keyword_testing_triggers_testing_qa(self, tmp_path):
        """Recipe containing 'testing' should include testing-qa specialist."""
        recipe = make_recipe(tmp_path, "Add testing coverage for this module.")
        rc, out, _ = run_assign(recipe)
        assert rc == 0
        specialists = out.splitlines()
        assert "testing-qa" in specialists

    def test_platform_ios_adds_platform_specialist(self, tmp_path):
        """Passing --platforms '["ios"]' should add platform-ios-apple."""
        recipe = make_recipe(tmp_path, "A basic feature recipe.")
        rc, out, _ = run_assign(recipe, platforms=["ios"])
        assert rc == 0
        specialists = out.splitlines()
        assert "platform-ios-apple" in specialists

    def test_platform_web_adds_frontend_and_backend(self, tmp_path):
        """Passing --platforms '["web"]' should add both web platform specialists."""
        recipe = make_recipe(tmp_path, "A basic feature recipe.")
        rc, out, _ = run_assign(recipe, platforms=["web"])
        assert rc == 0
        specialists = out.splitlines()
        assert "platform-web-frontend" in specialists
        assert "platform-web-backend" in specialists

    def test_platform_android_adds_android_specialist(self, tmp_path):
        """Passing --platforms '["android"]' should add platform-android."""
        recipe = make_recipe(tmp_path, "A basic feature recipe.")
        rc, out, _ = run_assign(recipe, platforms=["android"])
        assert rc == 0
        specialists = out.splitlines()
        assert "platform-android" in specialists

    def test_output_is_deduplicated(self, tmp_path):
        """Multiple keyword hits for the same specialist should not produce duplicates."""
        # 'auth' and 'tokens' and 'credentials' all map to 'security'
        recipe = make_recipe(
            tmp_path,
            "Handle auth with tokens and store credentials securely.",
        )
        rc, out, _ = run_assign(recipe)
        assert rc == 0
        specialists = out.splitlines()
        assert specialists.count("security") == 1, (
            f"'security' appeared {specialists.count('security')} times; expected 1"
        )

    def test_tier_order_sorts_output(self, tmp_path):
        """--tier-order should sort specialists by build tier."""
        # Use keywords that hit multiple specialists at different tiers:
        # 'database' -> data-persistence (tier 2)
        # 'auth' -> security (tier 4)
        # 'test' -> testing-qa (tier 8)
        recipe = make_recipe(
            tmp_path,
            "A recipe with auth flows, database access, and test coverage.",
        )
        rc, out, _ = run_assign(recipe, tier_order=True)
        assert rc == 0
        specialists = out.splitlines()

        # Load tier order from the mapping to verify
        mapping_path = PLUGIN_ROOT / "docs" / "research" / "specialist-assignment.json"
        mapping = json.loads(mapping_path.read_text())
        tier_list = mapping["tier-order"]

        def tier_index(s):
            try:
                return tier_list.index(s)
            except ValueError:
                return 999

        tier_indices = [tier_index(s) for s in specialists]
        assert tier_indices == sorted(tier_indices), (
            f"Specialists are not in tier order: {specialists}"
        )

    def test_tier_order_without_flag_is_alphabetical(self, tmp_path):
        """Without --tier-order, specialists should be sorted alphabetically."""
        recipe = make_recipe(
            tmp_path,
            "auth database test network API",
        )
        rc, out, _ = run_assign(recipe)
        assert rc == 0
        specialists = out.splitlines()
        assert specialists == sorted(specialists), (
            f"Expected alphabetical output, got: {specialists}"
        )

    def test_nonexistent_recipe_file_errors(self, tmp_path):
        """Passing a nonexistent recipe path should cause a non-zero exit code."""
        nonexistent = tmp_path / "does-not-exist.md"
        rc, _, _ = run_assign(nonexistent)
        assert rc != 0, "Expected non-zero exit code for missing recipe file"

    def test_recipe_with_no_keywords_produces_no_output(self, tmp_path):
        """A recipe with no matching keywords and no platforms should produce no output."""
        recipe = make_recipe(
            tmp_path,
            "This is a completely generic recipe with no specific technology mentions.",
        )
        rc, out, _ = run_assign(recipe)
        # Script exits 0 with no output when no specialists are matched
        assert out == "", f"Expected empty output, got: {out!r}"

    def test_multiple_platforms_combined(self, tmp_path):
        """Passing multiple platforms should include all their specialists."""
        recipe = make_recipe(tmp_path, "A basic feature recipe.")
        rc, out, _ = run_assign(recipe, platforms=["ios", "android"])
        assert rc == 0
        specialists = out.splitlines()
        assert "platform-ios-apple" in specialists
        assert "platform-android" in specialists

    def test_category_mapping_ui_domain(self, tmp_path):
        """Recipe with a ui domain in frontmatter should include ui-ux-design and accessibility."""
        content = "---\ndomain: cookbook/recipes/ui/colors/recipe.md\n---\nThis recipe styles a color picker."
        recipe = make_recipe(tmp_path, content)
        rc, out, _ = run_assign(recipe)
        assert rc == 0
        specialists = out.splitlines()
        assert "ui-ux-design" in specialists
        assert "accessibility" in specialists
