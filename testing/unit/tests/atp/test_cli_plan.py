"""atp CLI — `plan` subcommand.

Exercises the full wire: subprocess → CLI → plan_realizer → arbitrator.
Uses the plan_fixture team under testing/fixtures/teams/ so no real
planner is required.
"""
from __future__ import annotations

import asyncio
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
ATP_CLI = REPO_ROOT / "skills" / "atp" / "scripts" / "atp_cli.py"
FIXTURES_ROOT = REPO_ROOT / "testing" / "fixtures" / "teams"


ROADMAP_ID_RE = re.compile(r"^rm_[a-f0-9]+$")


def test_atp_plan_mock_prints_roadmap_id(tmp_path):
    db = tmp_path / "atp.sqlite"
    r = subprocess.run(
        [
            sys.executable,
            str(ATP_CLI),
            "--teams-root",
            str(FIXTURES_ROOT),
            "plan",
            "plan_fixture",
            "--goal",
            "build a tiny thing",
            "--dispatcher",
            "mock",
            "--db",
            str(db),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert r.returncode == 0, r.stderr
    stdout = r.stdout.strip().splitlines()
    assert len(stdout) == 1, f"expected one-line stdout, got {stdout!r}"
    roadmap_id = stdout[0]
    assert ROADMAP_ID_RE.match(roadmap_id), roadmap_id
    assert db.is_file()

    # Inspect the arbitrator directly to confirm plan_nodes landed.
    sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))
    from services.conductor.arbitrator import Arbitrator
    from services.conductor.arbitrator.backends import SqliteBackend

    async def _inspect() -> int:
        backend = SqliteBackend(db)
        arb = Arbitrator(backend)
        await arb.start()
        try:
            nodes = await arb.list_plan_nodes(roadmap_id)
        finally:
            await arb.close()
        return len(nodes)

    count = asyncio.run(_inspect())
    # Fixture team has 2 specialities; mock emits one plan_node each.
    assert count == 2, f"expected 2 plan_nodes, got {count}"


def test_atp_plan_requires_planner(tmp_path):
    """Team without team-leads/planner.md must be rejected with a clear error."""
    stub_root = tmp_path / "teams"
    team_dir = stub_root / "no_planner"
    (team_dir / "specialists" / "x" / "specialities").mkdir(parents=True)
    (team_dir / "team.md").write_text("---\nname: no_planner\n---\n")
    (team_dir / "specialists" / "x" / "specialities" / "y.md").write_text(
        "---\nname: y\ndescription: stub\n---\n\n## Worker Focus\n\nstub.\n"
    )

    r = subprocess.run(
        [
            sys.executable,
            str(ATP_CLI),
            "--teams-root",
            str(stub_root),
            "plan",
            "no_planner",
            "--goal",
            "X",
            "--dispatcher",
            "mock",
            "--db",
            str(tmp_path / "atp.sqlite"),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert r.returncode != 0
    assert "planner" in r.stderr.lower()
