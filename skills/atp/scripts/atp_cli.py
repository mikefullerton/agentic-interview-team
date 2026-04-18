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
from services.conductor.playbooks import name_a_puppy_roadmap  # noqa: E402
from services.conductor.specialty import WhatsNextSpecialty  # noqa: E402
from services.conductor.team_loader import TeamManifest, load_team  # noqa: E402


# ---------------------------------------------------------------------------
# Per-team overrides — teams whose roadmap + realizer are hand-authored,
# not derived from the generic one-node-per-specialty scaffold.
# ---------------------------------------------------------------------------

TEAM_OVERRIDES: dict[str, object] = {
    "puppynamingteam": {
        "module": name_a_puppy_roadmap,
        "build_roadmap": name_a_puppy_roadmap.build_roadmap,
        "realize": name_a_puppy_roadmap.realize,
        "interview_realize": name_a_puppy_roadmap.make_realizer(interview=True),
        "team_id": name_a_puppy_roadmap.TEAM_ID,
        "worker_agents": [
            "breed-name-worker",
            "lifestyle-name-worker",
            "temperament-name-worker",
            "aggregator-worker",
        ],
    },
}


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


def _build_dispatcher(
    name: str,
    manifest: TeamManifest,
    override: dict | None = None,
) -> Dispatcher:
    if name == "claude-code":
        return ClaudeCodeDispatcher()
    if name == "mock":
        # Scheduler mock: when called for a non-deterministic decision,
        # delegate to _mock_scheduler_decide which picks the first
        # runnable primitive by reading the prompt's plan-node list.
        responses: dict[str, object] = {
            "whats-next-worker": _mock_scheduler_decide,
            "whats-next-verifier": {"verdict": "pass", "reason": "mock"},
        }
        if override is not None:
            for agent in override.get("worker_agents", []):
                if "aggregator" in agent:
                    responses[agent] = {
                        "ranked_candidates": [
                            "Luna", "Biscuit", "Scout", "Daisy", "Rex",
                        ]
                    }
                else:
                    responses[agent] = {
                        "candidates": ["Mock", "Demo", "Placeholder"]
                    }
        else:
            for specialist in manifest.specialists.values():
                for specialty in specialist.specialties.values():
                    agent = f"{specialist.name}-{specialty.name}-worker"
                    responses[agent] = {
                        "result": {"mock": True, "specialty": specialty.name}
                    }
        return MockDispatcher(responses)
    raise SystemExit(f"atp: unknown dispatcher {name!r}")


async def _stdin_gate_answerer(arb, session_id, team_id):
    """Poll the session for open question gates; prompt the user on stdin
    and resolve each gate with their reply. Exits when the session
    reaches a terminal status so the conductor can finish cleanly."""
    seen: set[str] = set()
    loop = asyncio.get_event_loop()
    while True:
        session_row = await arb._storage.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        if session_row and session_row["status"] in (
            "completed",
            "failed",
            "aborted",
        ):
            return

        open_gates = await arb.list_gates(
            session_id, only_open=True, category="question"
        )
        for g in open_gates:
            gid = g["gate_id"]
            if gid in seen:
                continue
            seen.add(gid)
            # Find the most recent question message on this plan_node.
            messages = await arb.list_messages(session_id, team_id=team_id)
            body = ""
            for m in messages:
                if (
                    m.type == "question"
                    and m.plan_node_id == g.get("plan_node_id")
                ):
                    body = m.body
            options = json.loads(g.get("options_json") or "[]")
            prompt = f"\n? {body}"
            if options:
                prompt += f"  (options: {'/'.join(options)})"
            prompt += "\n> "
            print(prompt, end="", flush=True)
            # Read one line from stdin off the event loop.
            answer = await loop.run_in_executor(
                None, lambda: sys.stdin.readline().strip()
            )
            if not answer:
                answer = options[0] if options else ""
            await arb.resolve_gate(gid, verdict=answer)
        await asyncio.sleep(0.1)


def _mock_scheduler_decide(prompt: str) -> dict:
    """Parse the scheduler's prompt to find the plan-node list + latest
    state, then return an advance-to for the first un-done node, or
    `done` if everything is done."""
    import re
    # Prompt includes "Plan nodes: [...]" and "Latest state per node: {...}"
    pn_match = re.search(r"Plan nodes:\s*(\[.*?\])", prompt, re.DOTALL)
    st_match = re.search(r"Latest state per node:\s*(\{.*?\})", prompt, re.DOTALL)
    try:
        plan_nodes = json.loads(pn_match.group(1)) if pn_match else []
        state_map = json.loads(st_match.group(1)) if st_match else {}
    except Exception:
        plan_nodes, state_map = [], {}

    for n in plan_nodes:
        nid = n.get("node_id")
        if state_map.get(nid) not in ("done", "failed", "superseded"):
            return {
                "action": "advance-to",
                "node_id": nid,
                "reason": f"mock picks {nid}",
                "deterministic": False,
            }
    return {
        "action": "done",
        "node_id": None,
        "reason": "mock: nothing left",
        "deterministic": False,
    }


async def _run_team(
    manifest: TeamManifest,
    dispatcher_name: str,
    db_path: Path,
    team_name: str,
    interview: bool = False,
) -> int:
    backend = SqliteBackend(db_path)
    arb = Arbitrator(backend)
    await arb.start()

    override = TEAM_OVERRIDES.get(team_name)
    if override is not None:
        roadmap_id = await override["build_roadmap"](arb)
        if interview and "interview_realize" in override:
            realizer = override["interview_realize"]
        else:
            realizer = override["realize"]
        team_id = override["team_id"]
    else:
        # Generic fallback: one-node-per-specialty demo roadmap. Real
        # planning roadmaps are produced by `atp plan` (follow-up).
        roadmap = await arb.create_roadmap(f"{manifest.name}-demo")
        roadmap_id = roadmap.roadmap_id
        prev_node_id: str | None = None
        for specialist in manifest.specialists.values():
            for specialty in specialist.specialties.values():
                node_id = f"{specialist.name}.{specialty.name}"
                await arb.create_plan_node(
                    roadmap_id=roadmap_id,
                    title=f"{specialist.name} → {specialty.name}",
                    node_kind=NodeKind.PRIMITIVE,
                    node_id=node_id,
                    specialist=specialist.name,
                    speciality=specialty.name,
                )
                if prev_node_id is not None:
                    await arb.add_dependency(node_id, prev_node_id)
                prev_node_id = node_id
        realizer = make_generic_realizer(manifest)
        team_id = manifest.name

    session_id = uuid4()
    await arb.open_session(
        session_id,
        initial_team_id=team_id,
        roadmap_id=roadmap_id,
    )

    dispatcher = _build_dispatcher(dispatcher_name, manifest, override)
    conductor = Conductor(
        arbitrator=arb,
        dispatcher=dispatcher,
        team_lead=None,
        session_id=session_id,
        max_steps=500,
    )
    # Run the conductor concurrently with a stdin-based gate answerer.
    # Any question gate the realizer opens is rendered to stdout; the
    # user's reply on stdin resolves the gate so the conductor resumes.
    await asyncio.gather(
        conductor.run_roadmap(
            [WhatsNextSpecialty()], realize_primitive=realizer
        ),
        _stdin_gate_answerer(arb, session_id, team_id),
    )

    # Print a short summary including the final presented message, if any.
    messages = await arb.list_messages(session_id, team_id=team_id)
    final = messages[-1].body if messages else ""
    print(
        json.dumps(
            {
                "session_id": str(session_id),
                "roadmap_id": roadmap_id,
                "team": manifest.name,
                "dispatcher": dispatcher_name,
                "db": str(db_path),
                "final_message": final,
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
    interview: bool = False,
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
    return asyncio.run(
        _run_team(manifest, dispatcher_name, db_path, team_name, interview)
    )


def cmd_rollcall(
    teams_root: Path,
    team: str | None,
    output_format: str,
    concurrency: int,
    timeout: float,
) -> int:
    """Ping every role in one or all teams.

    v1 uses a scripted in-process runner — proves discovery + integration
    surface + formatting end to end without an LLM call. Real-LLM variant
    is the functional smoke (see 2026-04-18-rollcall-design.md task 5).
    """
    from services.integration_surface import InProcessSession
    from services.rollcall import (
        discover_team,
        discover_teams,
        render_json,
        render_table,
        roll_call,
    )

    if team is not None:
        team_dir = teams_root / team
        if not team_dir.is_dir():
            print(
                f"atp: no team {team!r} under {teams_root}", file=sys.stderr
            )
            return 2
        roles = discover_team(team_dir)
    else:
        if not teams_root.is_dir():
            print(
                f"atp: no teams directory at {teams_root}", file=sys.stderr
            )
            return 2
        roles = discover_teams(teams_root)

    if not roles:
        print("atp: no roles discovered", file=sys.stderr)
        return 2

    async def scripted_runner(io, user_turn, ctx):
        await io.emit("state", {"phase": "starting"})
        await io.emit(
            "text",
            {"text": f"roll-call ack ({ctx.team})"},
        )
        await io.emit("result", {"stop_reason": "end_turn"})

    session = InProcessSession(scripted_runner)
    results = asyncio.run(roll_call(
        session, roles, concurrency=concurrency, timeout=timeout,
    ))

    if output_format == "json":
        sys.stdout.write(render_json(results))
    else:
        sys.stdout.write(render_table(results))
    sys.stdout.flush()

    failures = [r for r in results if r.error is not None]
    return 0 if not failures else 2


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
    p_run.add_argument(
        "--interview",
        action="store_true",
        help="Use the team's interview realizer (asks user questions via stdin) if available.",
    )

    p_roll = sub.add_parser(
        "rollcall",
        help="Ping every role in one or all teams via the integration surface.",
    )
    p_roll.add_argument("team", nargs="?", default=None)
    p_roll.add_argument(
        "--format", choices=["table", "json"], default="table"
    )
    p_roll.add_argument("--concurrency", type=int, default=4)
    p_roll.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Per-role timeout in seconds (default 30).",
    )

    args = parser.parse_args(argv)
    teams_root = args.teams_root or _default_teams_root()

    if args.command == "list":
        return cmd_list(teams_root)
    if args.command == "describe":
        return cmd_describe(teams_root, args.team)
    if args.command == "run":
        args.db.parent.mkdir(parents=True, exist_ok=True)
        return cmd_run(
            teams_root, args.team, args.dispatcher, args.db, args.interview
        )
    if args.command == "rollcall":
        return cmd_rollcall(
            teams_root, args.team, args.format,
            args.concurrency, args.timeout,
        )

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
