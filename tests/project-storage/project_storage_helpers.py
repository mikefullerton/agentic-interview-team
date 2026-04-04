"""Helper functions for project-storage contract tests."""
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
PROJECT_STORAGE = str(REPO_ROOT / "plugins" / "dev-team" / "scripts" / "project_storage.py")


def run_storage(*args):
    """Call project_storage.py and return the CompletedProcess."""
    result = subprocess.run(
        ["python3", PROJECT_STORAGE] + list(args),
        capture_output=True, text=True
    )
    return result


def run_ok(*args):
    """Call project-storage.sh, assert success, return stdout."""
    result = run_storage(*args)
    assert result.returncode == 0, f"project-storage failed: {result.stderr}"
    return result.stdout.strip()


def run_json(*args):
    """Call project-storage.sh, assert success, return parsed JSON."""
    stdout = run_ok(*args)
    return json.loads(stdout)


def make_project(path, name="test-project"):
    """Init a project and return the parsed output."""
    return run_json(
        "project", "init",
        "--name", name,
        "--description", "Test project",
        "--path", str(path),
    )
