"""atp CLI smoke tests — exercise the three subcommands end-to-end."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
ATP_CLI = REPO_ROOT / "skills" / "atp" / "scripts" / "atp_cli.py"
TEAMS_ROOT = REPO_ROOT / "teams"


def _run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ATP_CLI), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd or REPO_ROOT),
    )


def test_atp_list_reports_known_teams():
    r = _run("--teams-root", str(TEAMS_ROOT), "list")
    assert r.returncode == 0, r.stderr
    teams = set(r.stdout.split())
    assert "devteam" in teams
    assert "puppynamingteam" in teams


def test_atp_describe_shows_specialists():
    r = _run("--teams-root", str(TEAMS_ROOT), "describe", "puppynamingteam")
    assert r.returncode == 0, r.stderr
    assert "team: puppynamingteam" in r.stdout
    assert "specialists:" in r.stdout


def test_atp_run_mock_produces_session(tmp_path):
    db = tmp_path / "atp.sqlite"
    r = _run(
        "--teams-root",
        str(TEAMS_ROOT),
        "run",
        "puppynamingteam",
        "--dispatcher",
        "mock",
        "--db",
        str(db),
    )
    assert r.returncode == 0, r.stderr
    # stdout has JSON; if the run printed anything before (shouldn't
    # here without --interview) grab the last { onwards.
    payload = json.loads(r.stdout[r.stdout.rfind("{"):])
    assert payload["team"] == "puppynamingteam"
    assert payload["dispatcher"] == "mock"
    assert db.is_file(), "sqlite file was not created"
    assert "Top candidate names:" in payload["final_message"]


def test_atp_run_puppy_interview_via_stdin(tmp_path):
    """Piping 4 answers on stdin drives the interview realizer through
    4 question gates and lands the session with a ranked list."""
    db = tmp_path / "atp.sqlite"
    r = subprocess.run(
        [
            sys.executable,
            str(ATP_CLI),
            "--teams-root",
            str(TEAMS_ROOT),
            "run",
            "puppynamingteam",
            "--dispatcher",
            "mock",
            "--interview",
            "--db",
            str(db),
        ],
        input="labrador\nmale\nblack\nplayful\n",
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert r.returncode == 0, r.stderr
    # Questions were emitted to stdout above the JSON payload.
    assert "breed" in r.stdout.lower()
    payload = json.loads(r.stdout[r.stdout.rfind("{"):])
    assert payload["team"] == "puppynamingteam"
    assert "Top candidate names:" in payload["final_message"]
