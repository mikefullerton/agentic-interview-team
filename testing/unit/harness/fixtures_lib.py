"""
Fixture management for interview tests.

Python reimplementation of tests/harness/lib/fixtures.ts.

Creates temp directories for fake projects (the cwd for tests)
and provides path helpers to repo roots and config files.
"""

import os
import shutil
import tempfile
from pathlib import Path

# ── Repo root paths ───────────────────────────────────────────────────

# testing/unit/harness/fixtures_lib.py → go up three levels to reach repo root
_HARNESS_DIR = Path(__file__).parent
_UNIT_DIR = _HARNESS_DIR.parent
_TESTING_DIR = _UNIT_DIR.parent

REPO_ROOT = _TESTING_DIR.parent  # dev-team repo root
PLUGIN_ROOT = REPO_ROOT / "plugins" / "dev-team"
TEST_OUTPUT = Path.home() / "projects" / "tests" / "dev-team-tests"
TEST_OUTPUT.mkdir(parents=True, exist_ok=True)
(TEST_OUTPUT / "config").mkdir(parents=True, exist_ok=True)
TEST_CONFIG_PATH = TEST_OUTPUT / "config" / "test-config.json"

# ── Fake project creation ─────────────────────────────────────────────


def create_fake_project(name: str) -> str:
    """
    Create a temporary fake project directory to serve as cwd.

    Initialises a bare .git so the skill can infer a project name.
    Returns the path to the created directory as a string.
    """
    dest = tempfile.mkdtemp(prefix=f"interview-test-{name}-")

    # Create a minimal git repo so the skill can infer the project
    git_dir = Path(dest, ".git")
    git_dir.mkdir()
    (git_dir / "config").write_text(
        "[core]\n\trepositoryformatversion = 0\n", encoding="utf-8"
    )
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

    # Write a marker file so the skill knows the project name
    Path(dest, "README.md").write_text(
        f"# {name}\n\nTest project for interview system testing.\n",
        encoding="utf-8",
    )

    return dest


def cleanup(path) -> None:
    """
    Remove a temp directory.

    Safe no-op when path is None/undefined or outside the system temp dir.
    """
    if path is None:
        return
    tmp = tempfile.gettempdir()
    if str(path).startswith(tmp):
        shutil.rmtree(path, ignore_errors=True)


# ── Path helpers ──────────────────────────────────────────────────────


def persona_path(name: str) -> str:
    """Resolve a persona filename to its absolute path under testing/functional/harness/fixtures/personas/."""
    return str(_TESTING_DIR / "functional" / "harness" / "fixtures" / "personas" / name)
