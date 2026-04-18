"""Rollcall unit tests — discovery, orchestrator, formatting, CLI."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from services.integration_surface import InProcessSession, validate_stream
from services.rollcall import (
    ROLL_CALL_PROMPT,
    RoleRef,
    discover_team,
    discover_teams,
    render_json,
    render_table,
    roll_call,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(
    REPO_ROOT / "testing" / "unit" / "tests" / "integration_surface"
))
from fixtures.fake_team import FakeTeam  # noqa: E402


EXPECTED_ROLES = {
    ("team-lead", "orchestrator"),
    ("team-lead", "planner"),
    ("specialty-worker", "architect.planning"),
    ("specialty-verifier", "architect.planning"),
    ("specialty-worker", "writer.drafting"),
    ("specialty-verifier", "writer.drafting"),
    ("specialty-worker", "reviewer.qa"),
    ("specialty-verifier", "reviewer.qa"),
}


def _scripted_team() -> FakeTeam:
    return FakeTeam().reply(
        ("state", {"phase": "starting"}),
        ("text", {"text": "hi"}),
        ("result", {"stop_reason": "end_turn"}),
    )


# ---- Task 1: discovery -----------------------------------------------------


def test_discovery_finds_all_eight_roles(fixture_team_root):
    roles = discover_team(fixture_team_root)
    assert len(roles) == 8
    assert {(r.kind, r.name) for r in roles} == EXPECTED_ROLES
    assert all(r.team == "rollcall_team" for r in roles)
    assert all(r.path.is_file() for r in roles)


def test_discover_teams_walks_multiple_teams(tmp_path, fixture_team_root):
    teams_root = tmp_path / "teams"
    teams_root.mkdir()
    # Symlink to avoid copying; discover_teams only reads file tree.
    (teams_root / "rollcall_team").symlink_to(fixture_team_root)
    (teams_root / "empty_team").mkdir()
    roles = discover_teams(teams_root)
    assert len(roles) == 8
    assert {r.team for r in roles} == {"rollcall_team"}


# ---- Task 2: orchestrator --------------------------------------------------


def test_roll_call_opens_one_session_per_role_all_ok(
    fixture_team_root, run_async
):
    team = _scripted_team()
    session = InProcessSession(team)
    roles = discover_team(fixture_team_root)

    results = run_async(roll_call(session, roles, concurrency=4))

    assert len(results) == 8
    assert all(r.error is None for r in results)
    assert all(r.response == "hi" for r in results)
    assert {(r.role.kind, r.role.name) for r in results} == EXPECTED_ROLES


def test_emitted_events_pass_schema_linter(fixture_team_root, run_async):
    session = InProcessSession(_scripted_team())
    roles = discover_team(fixture_team_root)
    results = run_async(roll_call(session, roles, concurrency=2))
    for r in results:
        assert validate_stream(list(r.events)) == []


def test_role_failure_is_isolated(fixture_team_root, run_async):
    """One failing role must not abort the run — the others still return ok."""
    scripted = _scripted_team()
    counter = {"n": 0}

    async def runner(io, user_turn, ctx):
        counter["n"] += 1
        if counter["n"] == 3:
            await io.emit("error", {"message": "synthetic"})
            return
        await scripted(io, user_turn, ctx)

    session = InProcessSession(runner)
    roles = discover_team(fixture_team_root)
    results = run_async(roll_call(session, roles, concurrency=1))

    failures = [r for r in results if r.error is not None]
    assert len(failures) == 1
    assert failures[0].error.message == "synthetic"
    assert sum(1 for r in results if r.error is None) == 7


# ---- Task 3: formatting ----------------------------------------------------


def test_render_json_one_line_per_role(fixture_team_root, run_async):
    session = InProcessSession(_scripted_team())
    roles = discover_team(fixture_team_root)
    results = run_async(roll_call(session, roles, concurrency=2))

    rendered = render_json(results)
    lines = [ln for ln in rendered.splitlines() if ln]
    assert len(lines) == 8
    for ln in lines:
        parsed = json.loads(ln)
        assert set(parsed.keys()) == {
            "team", "kind", "name", "status",
            "duration_ms", "response", "error",
        }
        assert parsed["status"] == "ok"
        assert parsed["response"] == "hi"
        assert parsed["error"] is None


def test_render_table_has_header_and_row_per_role(
    fixture_team_root, run_async
):
    session = InProcessSession(_scripted_team())
    roles = discover_team(fixture_team_root)
    results = run_async(roll_call(session, roles, concurrency=2))

    rendered = render_table(results)
    lines = rendered.splitlines()
    assert lines[0].startswith("TEAM")
    assert "ROLE" in lines[0]
    assert "STATUS" in lines[0]
    assert len(lines) == 1 + 8  # header + 8 rows
    assert all("ok" in ln for ln in lines[1:])


def test_render_table_shows_failed_and_reason(fixture_team_root, run_async):
    async def runner(io, user_turn, ctx):
        await io.emit("error", {"message": "kaput"})

    session = InProcessSession(runner)
    results = run_async(roll_call(
        session, discover_team(fixture_team_root), concurrency=1,
    ))
    rendered = render_table(results)
    assert "failed" in rendered
    assert "kaput" in rendered


# ---- CLI subcommand --------------------------------------------------------


def test_cli_rollcall_json_over_fixture_team(fixture_team_root):
    """End-to-end: the `atp rollcall` subcommand runs discovery, orchestrates
    the scripted runner, emits NDJSON, and exits 0."""
    import subprocess

    cli = REPO_ROOT / "skills" / "atp" / "scripts" / "atp_cli.py"
    teams_root = fixture_team_root.parent
    proc = subprocess.run(
        [
            sys.executable, str(cli),
            "--teams-root", str(teams_root),
            "rollcall", "rollcall_team",
            "--format", "json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    lines = [ln for ln in proc.stdout.splitlines() if ln]
    assert len(lines) == 8
    parsed = [json.loads(ln) for ln in lines]
    assert all(p["status"] == "ok" for p in parsed)
    assert {(p["kind"], p["name"]) for p in parsed} == EXPECTED_ROLES


# ---- Roll-call prompt contract --------------------------------------------


def test_roll_call_prompt_is_frozen():
    """If this test breaks, update the docs alongside the prompt change."""
    assert ROLL_CALL_PROMPT == (
        "You are participating in a roll-call. In one sentence, state: "
        "(a) your role, (b) the team you serve, (c) any readiness concerns."
    )
