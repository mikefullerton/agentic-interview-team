"""
Tests verifying that workflows and agents have been updated for the
codebase-decomposition and recipe specialist migration.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "dev-team"
WORKFLOWS_DIR = PLUGIN_ROOT / "skills" / "dev-team" / "workflows"
AGENTS_DIR = PLUGIN_ROOT / "agents"
DOCS_DIR = PLUGIN_ROOT / "docs"


# ---------------------------------------------------------------------------
# create-recipe-from-code workflow
# ---------------------------------------------------------------------------

class TestCreateRecipeFromCodeWorkflow:
    @pytest.fixture(autouse=True)
    def load_workflow(self):
        self.path = WORKFLOWS_DIR / "create-recipe-from-code.md"
        self.content = self.path.read_text(encoding="utf-8")

    def test_phase2_is_codebase_decomposition(self):
        assert "## Phase 2 — Codebase Decomposition" in self.content

    def test_phase2a_analytical_lenses(self):
        assert "### Phase 2a — Analytical Lenses" in self.content

    def test_phase2b_application_map_synthesis(self):
        assert "### Phase 2b — Application Map Synthesis" in self.content

    def test_references_decomposition_synthesizer_agent(self):
        assert "decomposition-synthesizer" in self.content

    def test_references_codebase_decomposition_specialist(self):
        assert "codebase-decomposition.md" in self.content

    def test_references_run_specialty_teams_script(self):
        assert "run_specialty_teams.py" in self.content

    def test_references_application_map_output(self):
        assert "application-map.md" in self.content

    def test_phase3_walks_bottom_up(self):
        assert "bottom-up" in self.content

    def test_phase3_references_recipe_order(self):
        assert "recipe order" in self.content.lower() or "recipe_order" in self.content

    def test_phase3_provides_child_recipe_paths(self):
        assert "Child recipe paths" in self.content or "child recipe" in self.content.lower()

    def test_phase4_passes_application_map(self):
        assert "Application map path" in self.content

    def test_no_scope_matcher_in_main_pipeline(self):
        # scope-matcher should only appear in the deprecation note, not as the main pipeline
        lines = self.content.split("\n")
        scope_matcher_lines = [
            i for i, ln in enumerate(lines)
            if "scope-matcher" in ln.lower() and "deprecated" not in ln.lower() and "note" not in ln.lower()
        ]
        # Allow references in the note block (blockquote lines starting with >)
        non_note_refs = [
            i for i in scope_matcher_lines
            if not lines[i].strip().startswith(">")
        ]
        assert len(non_note_refs) == 0, (
            f"scope-matcher referenced outside deprecation note at lines: {non_note_refs}"
        )

    def test_persistence_section_updated(self):
        assert "application map" in self.content.lower()
        assert "each team's findings" in self.content.lower() or "analytical lens" in self.content.lower()


# ---------------------------------------------------------------------------
# generate workflow
# ---------------------------------------------------------------------------

class TestGenerateWorkflow:
    @pytest.fixture(autouse=True)
    def load_workflow(self):
        self.path = WORKFLOWS_DIR / "generate.md"
        self.content = self.path.read_text(encoding="utf-8")

    def test_file_exists(self):
        assert self.path.exists()

    def test_references_specialty_team_pipeline(self):
        assert "run_specialty_teams.py" in self.content


# ---------------------------------------------------------------------------
# view-recipe workflow
# ---------------------------------------------------------------------------

class TestViewRecipeWorkflow:
    @pytest.fixture(autouse=True)
    def load_workflow(self):
        self.path = WORKFLOWS_DIR / "view-recipe.md"
        self.content = self.path.read_text(encoding="utf-8")

    def test_references_application_map(self):
        assert "application-map" in self.content

    def test_falls_back_to_scope_report(self):
        assert "scope-report" in self.content
        assert "fall back" in self.content.lower() or "older projects" in self.content.lower()

    def test_decomposition_category(self):
        assert '"decomposition"' in self.content


# ---------------------------------------------------------------------------
# project-assembler agent
# ---------------------------------------------------------------------------

class TestProjectAssemblerAgent:
    @pytest.fixture(autouse=True)
    def load_agent(self):
        self.path = AGENTS_DIR / "project-assembler.md"
        self.content = self.path.read_text(encoding="utf-8")

    def test_references_application_map(self):
        assert "application map" in self.content.lower() or "application-map" in self.content

    def test_no_scope_report_in_main_flow(self):
        # scope-report should not appear as a primary reference
        assert "scope report" not in self.content.lower() or "scope-report" not in self.content

    def test_context_references_application_map(self):
        assert "application-map" in self.content

    def test_uses_tree_hierarchy_from_map(self):
        assert "tree" in self.content.lower()

    def test_uses_depends_on_edges(self):
        assert "depends-on" in self.content


# ---------------------------------------------------------------------------
# Deprecation notices
# ---------------------------------------------------------------------------

class TestDeprecationNotices:
    def test_recipe_reviewer_has_deprecation_notice(self):
        path = AGENTS_DIR / "recipe-reviewer.md"
        content = path.read_text(encoding="utf-8")
        assert "DEPRECATED" in content
        assert "Recipe Specialist" in content or "recipe specialist" in content

    def test_scope_matcher_has_deprecation_notice(self):
        path = AGENTS_DIR / "scope-matcher.md"
        content = path.read_text(encoding="utf-8")
        assert "DEPRECATED" in content
        assert "Codebase Decomposition" in content or "codebase-decomposition" in content


# ---------------------------------------------------------------------------
# Architecture docs
# ---------------------------------------------------------------------------

class TestArchitectureDocs:
    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.path = REPO_ROOT / "docs" / "architecture.md"
        self.content = self.path.read_text(encoding="utf-8")

    def test_specialist_count_is_22(self):
        assert "22 specialists" in self.content

    def test_mentions_codebase_decomposition(self):
        assert "codebase-decomposition" in self.content

    def test_mentions_application_map(self):
        assert "Application Map" in self.content

    def test_mentions_application_map_spec(self):
        assert "application-map-spec.md" in self.content
