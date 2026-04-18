#!/usr/bin/env python3
"""atp CLI — minimal phase-1 subcommands: list, describe, run.

Usage:
    atp list [--teams-root <path>]
    atp describe <team> [--teams-root <path>]
    atp run <team> [--teams-root <path>] [--dispatcher mock|claude-code] [--db <path>]

Discovery: currently only `./teams/` (the project root's teams dir).
Wider discovery (~/.agentic-teams, ~/.claude/plugins/cache/) is a follow-up.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4


def _inject_services_path() -> Path:
    """Locate the conductor service package and extend sys.path. Returns
    the services root."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "plugins" / "dev-team"
        if (candidate / "services").is_dir():
            sys.path.insert(0, str(candidate))
            return candidate
    raise RuntimeError("could not locate plugins/dev-team from " + str(here))


_PLUGIN_ROOT = _inject_services_path()

from services.conductor.arbitrator import Arbitrator  # noqa: E402
from services.conductor.arbitrator.backends import SqliteBackend  # noqa: E402
from services.conductor.arbitrator.models import NodeKind  # noqa: E402
from services.conductor.conductor import Conductor  # noqa: E402
from services.conductor.dispatcher import (  # noqa: E402
    ClaudeCodeDispatcher,
    Dispatcher,
    MockDispatcher,
)
from services.conductor.generic_realizer import make_generic_realizer  # noqa: E402
from services.conductor.specialty import WhatsNextSpecialty  # noqa: E402
from services.conductor.team_loader import TeamManifest, load_team  # noqa: E402


DEFAULT_TEAMS_ROOT = Path.cwd() / "teams"


def _default_teams_root() -> Path:
    """Return ./teams if present, otherwise search up from the caller's CWD."""
    if DEFAULT_TEAMS_ROOT.is_dir():
        return DEFAULT_TEAMS_ROOT
    here = Path.cwd()
    for parent in [here] + list(here.parents):
        candidate = parent / "teams"
        if candidate.is_dir():
            return candidate
    return DEFAULT_TEAMS_ROOT


def cmd_list(teams_root: Path) -> int:
    if not teams_root.is_dir():
        print(f"atp: no teams directory at {teams_root}", file=sys.stderr)
        return 2
    teams = sorted(
        d.name for d in teams_root.iterdir() if d.is_dir() and (d / "team.md").is_file()
    )
    if not teams:
        print(f"atp: no teams under {teams_root}")
        return 0
    for name in teams:
        print(name)
    return 0


def cmd_describe(teams_root: Path, team_name: str) -> int:
    team_dir = teams_root / team_name
    if not team_dir.is_dir():
        print(f"atp: no team {team_name!r} under {teams_root}", file=sys.stderr)
        return 2
    manifest = load_team(team_dir)
    print(f"team: {manifest.name}")
    print(f"root: {manifest.team_root}")
    print(f"specialists: {len(manifest.specialists)}")
    for spec in manifest.specialists.values():
        names = ", ".join(sorted(spec.specialties.keys())) or "(none)"
        print(f"  - {spec.name}: {names}")
    return 0


def _build_dispatcher(name: str, manifest: TeamManifest) -> Dispatcher:
    if name == "claude-code":
        return ClaudeCodeDispatcher()
    if name == "mock":
        # Autogenerate canned responses for every worker in the manifest
        # plus the scheduler pair. Shape matches what the generic realizer
        # and whats-next specialty expect.
        responses: dict[str, object] = {
            "whats-next-worker": {
                "action": "done",
                "node_id": None,
                "reason": "mock end",
                "deterministic": False,
            },
            "whats-next-verifier": {"verdict": "pass", "reason": "mock"},
        }
        for specialist in manifest.specialists.values():
            for specialty in specialist.specialties.values():
                agent = f"{specialist.name}-{specialty.name}-worker"
                responses[agent] = {
                    "result": {"mock": True, "specialty": specialty.name}
                }
        return MockDispatcher(responses)
    raise SystemExit(f"atp: unknown dispatcher {name!r}")


async def _run_team(
    manifest: TeamManifest,
    dispatcher_name: str,
    db_path: Path,
) -> int:
    backend = SqliteBackend(db_path)
    arb = Arbitrator(backend)
    await arb.start()

    # Build a one-node-per-specialty demo roadmap. Real planning
    # roadmaps will be produced by atp plan (follow-up).
    roadmap = await arb.create_roadmap(f"{manifest.name}-demo")
    prev_node_id: str | None = None
    for specialist in manifest.specialists.values():
        for specialty in specialist.specialties.values():
            node_id = f"{specialist.name}.{specialty.name}"
            await arb.create_plan_node(
                roadmap_id=roadmap.roadmap_id,
                title=f"{specialist.name} → {specialty.name}",
                node_kind=NodeKind.PRIMITIVE,
                node_id=node_id,
                specialist=specialist.name,
                speciality=specialty.name,
            )
            if prev_node_id is not None:
                await arb.add_dependency(node_id, prev_node_id)
            prev_node_id = node_id

    session_id = uuid4()
    await arb.open_session(
        session_id,
        initial_team_id=manifest.name,
        roadmap_id=roadmap.roadmap_id,
    )

    dispatcher = _build_dispatcher(dispatcher_name, manifest)
    conductor = Conductor(
        arbitrator=arb,
        dispatcher=dispatcher,
        team_lead=None,
        session_id=session_id,
        max_steps=500,
    )
    await conductor.run_roadmap(
        [WhatsNextSpecialty()],
        realize_primitive=make_generic_realizer(manifest),
    )

    print(
        json.dumps(
            {
                "session_id": str(session_id),
                "roadmap_id": roadmap.roadmap_id,
                "team": manifest.name,
                "dispatcher": dispatcher_name,
                "db": str(db_path),
            },
            indent=2,
        )
    )
    await arb.close()
    return 0


def cmd_run(
    teams_root: Path,
    team_name: str,
    dispatcher_name: str,
    db_path: Path,
) -> int:
    team_dir = teams_root / team_name
    if not team_dir.is_dir():
        print(f"atp: no team {team_name!r} under {teams_root}", file=sys.stderr)
        return 2
    manifest = load_team(team_dir)
    if not manifest.specialists:
        print(
            f"atp: team {team_name!r} has no parseable specialties",
            file=sys.stderr,
        )
        return 2
    return asyncio.run(_run_team(manifest, dispatcher_name, db_path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="atp")
    parser.add_argument("--teams-root", type=Path, default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List discovered teams.")

    p_desc = sub.add_parser("describe", help="Show a team's manifest.")
    p_desc.add_argument("team")

    p_run = sub.add_parser("run", help="Run a one-node-per-specialty demo roadmap.")
    p_run.add_argument("team")
    p_run.add_argument(
        "--dispatcher", choices=["mock", "claude-code"], default="mock"
    )
    p_run.add_argument(
        "--db",
        type=Path,
        default=Path("./.atp/atp.sqlite"),
        help="SQLite path for the arbitrator (default ./.atp/atp.sqlite).",
    )

    args = parser.parse_args(argv)
    teams_root = args.teams_root or _default_teams_root()

    if args.command == "list":
        return cmd_list(teams_root)
    if args.command == "describe":
        return cmd_describe(teams_root, args.team)
    if args.command == "run":
        args.db.parent.mkdir(parents=True, exist_ok=True)
        return cmd_run(teams_root, args.team, args.dispatcher, args.db)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
