"""Helper functions for arbitrator contract tests."""
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
ARBITRATOR = str(REPO_ROOT / "plugins" / "dev-team" / "scripts" / "arbitrator.py")


def run_arbitrator(*args):
    """Call arbitrator.py and return the CompletedProcess."""
    result = subprocess.run(
        ["python3", ARBITRATOR] + list(args),
        capture_output=True, text=True
    )
    return result


def run_ok(*args):
    """Call arbitrator.sh, assert success, return stdout."""
    result = run_arbitrator(*args)
    assert result.returncode == 0, f"arbitrator failed: {result.stderr}"
    return result.stdout.strip()


def run_json(*args):
    """Call arbitrator.sh, assert success, return parsed JSON."""
    stdout = run_ok(*args)
    return json.loads(stdout)


def make_session(**kwargs):
    """Create a test session and return its ID."""
    data = run_json(
        "session", "create",
        "--playbook", kwargs.get("playbook", "test"),
        "--team-lead", kwargs.get("team_lead", "test"),
        "--user", kwargs.get("user", "testuser"),
        "--machine", kwargs.get("machine", "testhost"),
    )
    return data["session_id"]
