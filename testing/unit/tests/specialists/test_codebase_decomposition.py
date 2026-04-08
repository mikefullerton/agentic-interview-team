"""
Tests for the codebase-decomposition specialist, its 12 specialty teams,
the decomposition-synthesizer agent, and the application-map-spec.
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
TEAMS_DIR = PLUGIN_ROOT / "specialty-teams" / "codebase-decomposition"
AGENTS_DIR = PLUGIN_ROOT / "agents"
DOCS_DIR = PLUGIN_ROOT / "docs"
RUN_SCRIPT = PLUGIN_ROOT / "scripts" / "run_specialty_teams.py"
ASSIGN_SCRIPT = PLUGIN_ROOT / "scripts" / "assign_specialists.py"

COOKBOOK_ROOT = REPO_ROOT.parent / "cookbook"

EXPECTED_TEAMS = [
    "algorithmic-complexity",
    "app-interactions",
    "cross-cutting-detection",
    "dependency-clusters",
    "framework-conventions",
    "interface-cohesion",
    "lifecycle-patterns",
    "module-boundaries",
    "purpose-classification",
    "runtime-conditions",
    "system-dependencies",
    "system-interactions",
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


def run_specialty_teams():
    result = subprocess.run(
        ["python3", str(RUN_SCRIPT), str(SPECIALISTS_DIR / "codebase-decomposition.md")],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Specialist definition tests
# ---------------------------------------------------------------------------

class TestCodebaseDecompositionSpecialist:
    @pytest.fixture(autouse=True)
    def load_specialist(self):
        self.path = SPECIALISTS_DIR / "codebase-decomposition.md"
        self.content = self.path.read_text(encoding="utf-8")
        self.sections = parse_sections(self.content)

    def test_file_exists(self):
        assert self.path.exists()

    def test_title_matches_spec(self):
        assert self.content.startswith("# Codebase Decomposition Specialist")

    def test_has_role_section(self):
        assert "Role" in self.sections
        assert len(self.sections["Role"]) > 0

    def test_has_persona_section(self):
        assert "Persona" in self.sections
        assert "(coming)" not in self.sections["Persona"]

    def test_persona_has_required_subsections(self):
        persona = self.sections["Persona"]
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
        assert len(sources) == 12

    def test_has_manifest_with_12_teams(self):
        assert "Manifest" in self.sections
        paths = [
            ln.strip()[2:]
            for ln in self.sections["Manifest"].splitlines()
            if ln.strip().startswith("- ")
        ]
        assert len(paths) == 12

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
# Specialty-team file tests (targeted for codebase-decomposition)
# ---------------------------------------------------------------------------

class TestCodebaseDecompositionTeams:
    def test_directory_exists(self):
        assert TEAMS_DIR.is_dir()

    def test_has_exactly_12_teams(self):
        files = sorted(TEAMS_DIR.glob("*.md"))
        assert len(files) == 12, f"Expected 12, got {len(files)}: {[f.stem for f in files]}"

    def test_expected_team_names(self):
        files = sorted(f.stem for f in TEAMS_DIR.glob("*.md"))
        assert files == EXPECTED_TEAMS

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_team_has_valid_frontmatter(self, team_name):
        path = TEAMS_DIR / f"{team_name}.md"
        content = path.read_text(encoding="utf-8")
        fields, body = parse_frontmatter(content)
        assert fields is not None, f"{team_name}: Missing frontmatter"

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_team_name_matches_filename(self, team_name):
        path = TEAMS_DIR / f"{team_name}.md"
        fields, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        assert fields["name"] == team_name

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_team_artifact_points_to_correct_guideline(self, team_name):
        path = TEAMS_DIR / f"{team_name}.md"
        fields, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        expected_artifact = f"guidelines/codebase-decomposition/{team_name}.md"
        assert fields["artifact"] == expected_artifact

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
        assert len(match.group(1).strip()) > 20, "Worker Focus too short"

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_team_verify_non_empty(self, team_name):
        path = TEAMS_DIR / f"{team_name}.md"
        content = path.read_text(encoding="utf-8")
        match = re.search(r"## Verify\n([\s\S]*?)(?=\n## |\n*$)", content)
        assert match is not None
        assert len(match.group(1).strip()) > 20, "Verify too short"


# ---------------------------------------------------------------------------
# run_specialty_teams.py integration
# ---------------------------------------------------------------------------

class TestRunSpecialtyTeamsScript:
    @pytest.fixture(autouse=True)
    def load_data(self):
        self.data = run_specialty_teams()

    def test_returns_12_specialty_teams(self):
        assert len(self.data["specialty_teams"]) == 12

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

    def test_artifacts_point_to_codebase_decomposition_guidelines(self):
        for team in self.data["specialty_teams"]:
            assert team["artifact"].startswith("guidelines/codebase-decomposition/")


# ---------------------------------------------------------------------------
# Cookbook artifact existence (cross-repo)
# ---------------------------------------------------------------------------

class TestCookbookArtifacts:
    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_cookbook_guideline_exists(self, team_name):
        guideline_path = COOKBOOK_ROOT / "guidelines" / "codebase-decomposition" / f"{team_name}.md"
        if not COOKBOOK_ROOT.exists():
            pytest.skip("Cookbook repo not found at expected location")
        assert guideline_path.exists(), f"Missing cookbook artifact: {guideline_path}"

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_cookbook_guideline_has_frontmatter(self, team_name):
        guideline_path = COOKBOOK_ROOT / "guidelines" / "codebase-decomposition" / f"{team_name}.md"
        if not guideline_path.exists():
            pytest.skip("Cookbook guideline not found")
        content = guideline_path.read_text(encoding="utf-8")
        fields, body = parse_frontmatter(content)
        assert fields is not None, "Missing frontmatter in cookbook guideline"
        assert "title" in fields
        assert fields.get("type") == "guideline"

    @pytest.mark.parametrize("team_name", EXPECTED_TEAMS)
    def test_cookbook_guideline_has_required_sections(self, team_name):
        guideline_path = COOKBOOK_ROOT / "guidelines" / "codebase-decomposition" / f"{team_name}.md"
        if not guideline_path.exists():
            pytest.skip("Cookbook guideline not found")
        content = guideline_path.read_text(encoding="utf-8")
        assert "## Signals and Indicators" in content
        assert "## Boundary Detection" in content
        assert "## Findings Format" in content


# ---------------------------------------------------------------------------
# Decomposition-synthesizer agent tests
# ---------------------------------------------------------------------------

class TestDecompositionSynthesizerAgent:
    @pytest.fixture(autouse=True)
    def load_agent(self):
        self.path = AGENTS_DIR / "decomposition-synthesizer.md"
        self.content = self.path.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\n([\s\S]*?)\n---\n([\s\S]*)$", self.content)
        assert fm_match is not None
        self.frontmatter_raw = fm_match.group(1)
        self.body = fm_match.group(2)
        self.sections = parse_sections(self.content)

    def test_file_exists(self):
        assert self.path.exists()

    def test_name_is_decomposition_synthesizer(self):
        assert "name: decomposition-synthesizer" in self.frontmatter_raw

    def test_has_write_tool(self):
        assert "Write" in self.frontmatter_raw

    def test_has_read_tool(self):
        assert "Read" in self.frontmatter_raw

    def test_references_application_map_spec(self):
        assert "application-map-spec.md" in self.body

    def test_has_7_steps(self):
        for step_num in range(1, 8):
            assert f"### Step {step_num}" in self.body, f"Missing Step {step_num}"

    def test_step1_is_establish_tree(self):
        assert "### Step 1: Establish the Tree" in self.body

    def test_step2_is_map_files(self):
        assert "### Step 2: Map Files to Nodes" in self.body

    def test_step3_is_annotate(self):
        assert "### Step 3: Annotate Each Node" in self.body

    def test_step4_is_map_edges(self):
        assert "### Step 4: Map Edges" in self.body

    def test_step5_is_cross_cutting(self):
        assert "### Step 5: Identify Cross-Cutting Concerns" in self.body

    def test_step6_is_recipe_order(self):
        assert "### Step 6: Compute Recipe Order" in self.body

    def test_step7_is_granularity(self):
        assert "### Step 7: Determine Recipe Granularity" in self.body

    def test_references_all_12_lenses(self):
        for team_name in EXPECTED_TEAMS:
            assert team_name.replace("-", "-") in self.body or \
                team_name.replace("-", " ") in self.body, \
                f"Agent doesn't reference lens: {team_name}"


# ---------------------------------------------------------------------------
# Application map spec tests
# ---------------------------------------------------------------------------

class TestApplicationMapSpec:
    @pytest.fixture(autouse=True)
    def load_spec(self):
        self.path = DOCS_DIR / "application-map-spec.md"
        self.content = self.path.read_text(encoding="utf-8")
        self.sections = parse_sections(self.content)

    def test_file_exists(self):
        assert self.path.exists()

    def test_title(self):
        assert "# Application Map Specification" in self.content

    def test_has_version(self):
        assert "Version: 1.0.0" in self.content

    def test_has_purpose_section(self):
        assert "Purpose" in self.sections

    def test_has_frontmatter_section(self):
        assert "Frontmatter" in self.content

    def test_has_required_sections_section(self):
        assert "Required Sections" in self.content

    def test_defines_overview_section(self):
        assert "#### 1. Overview" in self.content

    def test_defines_file_index_section(self):
        assert "#### 2. File Index" in self.content

    def test_defines_tree_section(self):
        assert "#### 3. Tree" in self.content

    def test_defines_nodes_section(self):
        assert "#### 4. Nodes" in self.content

    def test_defines_feature_flows_section(self):
        assert "#### 5. Feature Flows" in self.content

    def test_defines_cross_cutting_section(self):
        assert "#### 6. Cross-Cutting Concerns" in self.content

    def test_has_structural_validation_rules(self):
        assert "### Structural (S-series)" in self.content

    def test_has_content_validation_rules(self):
        assert "### Content (C-series)" in self.content

    def test_has_s01_through_s08(self):
        for i in range(1, 9):
            assert f"S{i:02d}" in self.content, f"Missing validation rule S{i:02d}"

    def test_has_c01_through_c08(self):
        for i in range(1, 9):
            assert f"C{i:02d}" in self.content, f"Missing validation rule C{i:02d}"

    def test_has_cookbook_relationship_table(self):
        assert "## Relationship to Cookbook Project" in self.content

    def test_node_field_rules_table(self):
        assert "##### Node Field Rules" in self.content
