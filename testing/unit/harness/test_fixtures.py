"""
Unit tests for fixture utilities.

Tests fake project creation and cleanup.

Converted from testing/unit/harness/specs/unit/fixtures.test.ts.
"""

import os
import tempfile
from pathlib import Path

import pytest

from fixtures_lib import (
    PLUGIN_ROOT,
    REPO_ROOT,
    TEST_CONFIG_PATH,
    TEST_OUTPUT,
    cleanup,
    create_fake_project,
    persona_path,
)


# ── create_fake_project ───────────────────────────────────────────────

class TestCreateFakeProject:
    def setup_method(self):
        self.temp_dir = None

    def teardown_method(self):
        cleanup(self.temp_dir)

    def test_creates_a_temp_directory(self):
        self.temp_dir = create_fake_project("test-project")
        assert Path(self.temp_dir).exists()

    def test_creates_directory_in_system_temp(self):
        self.temp_dir = create_fake_project("test-project")
        assert self.temp_dir.startswith(tempfile.gettempdir())

    def test_includes_project_name_in_path(self):
        self.temp_dir = create_fake_project("my-app")
        assert "interview-test-my-app-" in self.temp_dir

    def test_creates_a_git_directory(self):
        self.temp_dir = create_fake_project("test-project")
        assert Path(self.temp_dir, ".git").exists()

    def test_creates_a_git_head_file(self):
        self.temp_dir = create_fake_project("test-project")
        head = Path(self.temp_dir, ".git", "HEAD").read_text(encoding="utf-8")
        assert "refs/heads/main" in head

    def test_creates_a_readme_with_project_name(self):
        self.temp_dir = create_fake_project("lumina")
        readme = Path(self.temp_dir, "README.md").read_text(encoding="utf-8")
        assert "lumina" in readme


# ── cleanup ───────────────────────────────────────────────────────────

class TestCleanup:
    def test_removes_a_temp_directory(self):
        temp_dir = create_fake_project("cleanup-test")
        assert Path(temp_dir).exists()
        cleanup(temp_dir)
        assert not Path(temp_dir).exists()

    def test_does_nothing_for_none(self):
        # Should not raise
        cleanup(None)

    def test_does_nothing_for_non_temp_paths(self):
        # Safety check — should not delete paths outside tmpdir
        cleanup("/usr/local/bin")
        assert Path("/usr/local/bin").exists()


# ── path helpers ──────────────────────────────────────────────────────

class TestPathHelpers:
    def test_repo_root_points_to_the_interview_team_repo(self):
        assert Path(REPO_ROOT, "plugins", "dev-team", "agents").exists()

    def test_test_config_path_points_to_the_test_config(self):
        # Config file is created by E2E tests; skip if not yet generated
        if not TEST_CONFIG_PATH.exists():
            pytest.skip("test config not yet generated (run E2E tests first)")
        assert TEST_CONFIG_PATH.exists()

    def test_persona_path_resolves_persona_files(self):
        path = persona_path("sarah-ios-photo-app.md")
        assert Path(path).exists()

    def test_persona_path_returns_absolute_path(self):
        path = persona_path("sarah-ios-photo-app.md")
        assert path.startswith("/")
