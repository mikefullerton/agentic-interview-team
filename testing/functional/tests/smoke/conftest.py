"""Shared fixtures for smoke tests."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "dev-team"
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"

ARBITRATOR = str(SCRIPTS_DIR / "arbitrator.py")
PROJECT_STORAGE = str(SCRIPTS_DIR / "project_storage.py")
STORAGE_PROVIDER = str(SCRIPTS_DIR / "storage_provider.py")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolated_session_dir(tmp_path):
    """Give every test its own ARBITRATOR_SESSION_BASE."""
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    os.environ["ARBITRATOR_SESSION_BASE"] = str(session_dir)
    yield session_dir
    os.environ.pop("ARBITRATOR_SESSION_BASE", None)


@pytest.fixture()
def project_path(tmp_path):
    """Return a temp path suitable for project init (no .dev-team-project yet)."""
    return tmp_path / "workspace"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_script(script, args, env=None):
    """Run a Python script as subprocess, return CompletedProcess."""
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [sys.executable, script] + list(args),
        capture_output=True,
        text=True,
        env=merged,
    )


def run_ok(script, args, env=None):
    """Run script, assert exit 0, return stdout."""
    result = run_script(script, args, env=env)
    assert result.returncode == 0, (
        f"Script failed (rc={result.returncode}):\n"
        f"  cmd: {script} {' '.join(args)}\n"
        f"  stderr: {result.stderr}"
    )
    return result.stdout.strip()


def run_json(script, args, env=None):
    """Run script, assert exit 0, return parsed JSON."""
    stdout = run_ok(script, args, env=env)
    return json.loads(stdout)
