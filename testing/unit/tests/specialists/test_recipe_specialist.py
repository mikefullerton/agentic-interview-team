"""
Tests for the recipe specialist, its 6 specialty teams,
universal assignment behavior, and cookbook artifact cross-references.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "dev-team"
SPECIALISTS_DIR = PLUGIN_ROOT / "specialists"
TEAMS_DIR = PLUGIN_ROOT / "specialty-teams" / "recipe"
ASSIGN_SCRIPT = PLUGIN_ROOT / "scripts" / "assign_specialists.py"
RUN_SCRIPT = PLUGIN_ROOT / "scripts" / "run_specialty_teams.py"
MAPPING_PATH = PLUGIN_ROOT / "docs" / "research" / "specialist-assignment.json"

COOKBOOK_ROOT = REPO_ROOT.parent / "cookbook"

EXPECTED_TEAMS = [
    "behavioral-requirements",
    "completeness",
    "cookbook-compliance",
    "cross-recipe-consistency",
    "source-fidelity",
    "template-conformance",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(content):
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


def parse_sections(md_text):
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


def run_assign(recipe_path, platforms=None, tier_order=False):
    import os
    cmd = [sys.executable, str(ASSIGN_SCRIPT), str(recipe_path)]
    if platforms:
        cmd += ["--platforms", json.dumps(platforms)]
    if tier_order:
        cmd += ["--tier-order"]
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def make_recipe(tmp_path, content, filename="recipe.md"):
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return p


def run_specialty_teams():
    result = subprocess.run(
        ["python3", str(RUN_SCRIPT), str(SPECIALISTS_DIR / "recipe.md")],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Specialist definition tests
# ---------------------------------------------------------------------------

class TestRecipeSpecialist:
    @pytest.fixture(autouse=True)
    def load_specialist(self):
        self.path = SPECIALISTS_DIR / "recipe.md"
        self.content = self.path.read_text(encoding="utf-8")
        self.sections = parse_sections(self.content)

    def test_file_exists(self):
        assert self.path.exists()

    def test_title_matches_spec(self):
        assert self.content.startswith("# Recipe Specialist")

    def test_has_role_section(self):
        assert "Role" in self.sections
        assert len(self.sections["Role"]) > 0

    def test_has_persona_section(self):
        assert "Persona" in self.sections
        assert "(coming)" not in self.sections["Persona"]

    def test_persona_has_required_subsections(self):
        assert "### Archetype" in self.content
        assert "### Voice" in self.content
        assert "### Priorities" in self.content

    def test_has_cookbook_sources(self):
        assert "Cookbook Sources" in self.sections
        sources = [
            ln.strip()[2:].strip("`")
            for ln in self.sections["Cookbook Sources"].splitlines()
            if ln.strip().startswith("- ")
        ]
        assert len(sources) == 6

    def test_has_manifest_with_6_teams(self):
        assert "Manifest" in self.sections
        paths = [
            ln.strip()[2:]
            for ln in self.sections["Manifest"].splitlines()
            if ln.strip().startswith("- ")
        ]
        assert len(paths) == 6

    def test_manifest_paths_all_resolve(self):
        paths = [
            ln.strip()[2:]
            for ln in self.sections["Manifest"].splitlines()
            if ln.strip().startswith("- ")
        ]
        for p in paths:
            assert (PLUGIN_ROOT / p).exists(), f"Manifest path missing: {p}"

    def test_has_exploratory_prompts(self):
        assert "Exploratory Prompts" in self.sections
        prompts = [
            ln
            for ln in self.sections["Exploratory Prompts"].splitlines()
            if ln.strip() and ln.strip()[0].isdigit()
        ]
        assert len(prompts) >= 2

    def test_no_consulting_teams(self):
        assert "Consulting Teams" not in self.sections


# ---------------------------------------------------------------------------
# Specialty-team file tests (targeted for recipe)
# ---------------------------------------------------------------------------

class TestRecipeTeams:
    def test_directory_exists(self):
        assert TEAMS_DIR.is_dir()

    def test_has_exactly_6_teams(self):
        files = sorted(TEAMS_DIR.glob("*.md"))
        assert len(files) == 6, f"Expected 6, got {len(files)}: {[f.stem for f in files]}"

    def test_expected_team_names(self):
        files = sorted(f.stem for f in TEAMS_DIR.glob("*.md"))
        assert files == EXPECTED_TEAMS

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_team_has_valid_frontmatter(self, team_name):
        path = TEAMS_DIR / f"{team_name}.md"
        fields, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        assert fields is not None

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_team_name_matches_filename(self, team_name):
        path = TEAMS_DIR / f"{team_name}.md"
        fields, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        assert fields["name"] == team_name

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_team_artifact_points_to_recipe_quality_guideline(self, team_name):
        path = TEAMS_DIR / f"{team_name}.md"
        fields, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        expected = f"guidelines/recipe-quality/{team_name}.md"
        assert fields["artifact"] == expected

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_team_has_worker_focus(self, team_name):
        path = TEAMS_DIR / f"{team_name}.md"
        content = path.read_text(encoding="utf-8")
        assert "## Worker Focus" in content

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_team_has_verify(self, team_name):
        path = TEAMS_DIR / f"{team_name}.md"
        content = path.read_text(encoding="utf-8")
        assert "## Verify" in content

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_team_worker_focus_non_empty(self, team_name):
        path = TEAMS_DIR / f"{team_name}.md"
        content = path.read_text(encoding="utf-8")
        match = re.search(r"## Worker Focus\n([\s\S]*?)(?=\n## |\n*$)", content)
        assert match is not None
        assert len(match.group(1).strip()) > 20

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_team_verify_non_empty(self, team_name):
        path = TEAMS_DIR / f"{team_name}.md"
        content = path.read_text(encoding="utf-8")
        match = re.search(r"## Verify\n([\s\S]*?)(?=\n## |\n*$)", content)
        assert match is not None
        assert len(match.group(1).strip()) > 20


# ---------------------------------------------------------------------------
# run_specialty_teams.py integration
# ---------------------------------------------------------------------------

class TestRunSpecialtyTeamsScript:
    @pytest.fixture(autouse=True)
    def load_data(self):
        self.data = run_specialty_teams()

    def test_returns_6_specialty_teams(self):
        assert len(self.data["specialty_teams"]) == 6

    def test_no_consulting_teams(self):
        assert self.data["consulting_teams"] == []

    def test_each_team_has_required_fields(self):
        for team in self.data["specialty_teams"]:
            assert "name" in team
            assert "artifact" in team
            assert "worker_focus" in team
            assert "verify" in team

    def test_team_names_match_expected(self):
        names = sorted(t["name"] for t in self.data["specialty_teams"])
        assert names == EXPECTED_TEAMS

    def test_artifacts_point_to_recipe_quality_guidelines(self):
        for team in self.data["specialty_teams"]:
            assert team["artifact"].startswith("guidelines/recipe-quality/")


# ---------------------------------------------------------------------------
# Universal specialist assignment
# ---------------------------------------------------------------------------

class TestUniversalAssignment:
    def test_mapping_file_has_universal_specialists(self):
        mapping = json.loads(MAPPING_PATH.read_text())
        assert "universal-specialists" in mapping
        assert "recipe" in mapping["universal-specialists"]

    def test_recipe_in_tier_order(self):
        mapping = json.loads(MAPPING_PATH.read_text())
        tier_order = mapping["tier-order"]
        assert "recipe" in tier_order

    def test_recipe_is_before_platform_specialists_in_tier(self):
        mapping = json.loads(MAPPING_PATH.read_text())
        tier_order = mapping["tier-order"]
        recipe_idx = tier_order.index("recipe")
        ios_idx = tier_order.index("platform-ios-apple")
        assert recipe_idx < ios_idx, "recipe should be before platform specialists"

    def test_generic_recipe_gets_recipe_specialist(self, tmp_path):
        recipe = make_recipe(
            tmp_path,
            "A completely generic recipe with no technology keywords.",
        )
        rc, out, _ = run_assign(recipe)
        assert rc == 0
        specialists = out.splitlines()
        assert "recipe" in specialists

    def test_keyword_recipe_also_gets_recipe_specialist(self, tmp_path):
        recipe = make_recipe(
            tmp_path,
            "This recipe handles auth via OAuth tokens and database storage.",
        )
        rc, out, _ = run_assign(recipe)
        assert rc == 0
        specialists = out.splitlines()
        assert "recipe" in specialists
        assert "security" in specialists
        assert "data-persistence" in specialists

    def test_recipe_specialist_appears_once(self, tmp_path):
        recipe = make_recipe(
            tmp_path,
            "Auth tokens database storage network API testing logging.",
        )
        rc, out, _ = run_assign(recipe)
        assert rc == 0
        specialists = out.splitlines()
        assert specialists.count("recipe") == 1

    def test_tier_order_places_recipe_correctly(self, tmp_path):
        recipe = make_recipe(
            tmp_path,
            "Auth tokens database storage network API.",
        )
        rc, out, _ = run_assign(recipe, tier_order=True)
        assert rc == 0
        specialists = out.splitlines()
        mapping = json.loads(MAPPING_PATH.read_text())
        tier_list = mapping["tier-order"]

        def tier_index(s):
            try:
                return tier_list.index(s)
            except ValueError:
                return 999

        indices = [tier_index(s) for s in specialists]
        assert indices == sorted(indices), f"Not in tier order: {specialists}"


# ---------------------------------------------------------------------------
# Cookbook artifact existence (cross-repo)
# ---------------------------------------------------------------------------

class TestRecipeCookbookArtifacts:
    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_cookbook_guideline_exists(self, team_name):
        path = COOKBOOK_ROOT / "guidelines" / "recipe-quality" / f"{team_name}.md"
        if not COOKBOOK_ROOT.exists():
            pytest.skip("Cookbook repo not found")
        assert path.exists(), f"Missing cookbook artifact: {path}"

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_cookbook_guideline_has_frontmatter(self, team_name):
        path = COOKBOOK_ROOT / "guidelines" / "recipe-quality" / f"{team_name}.md"
        if not path.exists():
            pytest.skip("Cookbook guideline not found")
        content = path.read_text(encoding="utf-8")
        fields, _ = parse_frontmatter(content)
        assert fields is not None
        assert "title" in fields
        assert fields.get("type") == "guideline"

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_cookbook_guideline_has_required_sections(self, team_name):
        path = COOKBOOK_ROOT / "guidelines" / "recipe-quality" / f"{team_name}.md"
        if not path.exists():
            pytest.skip("Cookbook guideline not found")
        content = path.read_text(encoding="utf-8")
        assert "## Requirements" in content
        assert "## Common Violations" in content
        assert "## Verification Checklist" in content
