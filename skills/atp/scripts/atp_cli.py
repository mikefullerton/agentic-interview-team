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
from services.integration_surface import (  # noqa: E402
    InProcessSession,
    run_cli,
)


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


async def _bridge_gate_questions(arb, session_id, team_id, io) -> None:
    """Poll the arbitrator for open question gates; surface each one on
    the integration surface via `io.ask(...)`, and resolve the gate with
    the host's reply. Exits when the session reaches a terminal status.
    """
    seen: set[str] = set()
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
            messages = await arb.list_messages(session_id, team_id=team_id)
            body = ""
            for m in messages:
                if (
                    m.type == "question"
                    and m.plan_node_id == g.get("plan_node_id")
                ):
                    body = m.body
            answer = await io.ask(gid, "user", body)
            if not answer:
                options = json.loads(g.get("options_json") or "[]")
                answer = options[0] if options else ""
            await arb.resolve_gate(gid, verdict=answer)
        await asyncio.sleep(0.05)


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


async def _build_roadmap_and_realizer(
    arb: Arbitrator,
    manifest: TeamManifest,
    team_name: str,
    interview: bool,
):
    """Set up (roadmap_id, realizer, team_id, override) for a team. Uses
    the hand-authored override when the team has one, otherwise builds a
    generic one-node-per-specialty demo roadmap."""
    override = TEAM_OVERRIDES.get(team_name)
    if override is not None:
        roadmap_id = await override["build_roadmap"](arb)
        if interview and "interview_realize" in override:
            realizer = override["interview_realize"]
        else:
            realizer = override["realize"]
        team_id = override["team_id"]
        return roadmap_id, realizer, team_id, override

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
    return roadmap_id, realizer, manifest.name, None


def _make_conductor_runner(
    manifest: TeamManifest,
    dispatcher_name: str,
    db_path: Path,
    team_name: str,
    interview: bool,
):
    """Return a TeamRunner that, when invoked, drives the conductor
    end-to-end for one team and streams progress + final output back
    through the integration surface as protocol events."""

    async def runner(io, user_turn, ctx):
        backend = SqliteBackend(db_path)
        arb = Arbitrator(backend)
        await arb.start()
        try:
            roadmap_id, realizer, team_id, override = (
                await _build_roadmap_and_realizer(
                    arb, manifest, team_name, interview
                )
            )
            session_id = uuid4()
            await arb.open_session(
                session_id,
                initial_team_id=team_id,
                roadmap_id=roadmap_id,
            )

            await io.emit(
                "state",
                {
                    "phase": "starting",
                    "team": manifest.name,
                    "dispatcher": dispatcher_name,
                    "session_id": str(session_id),
                    "roadmap_id": roadmap_id,
                },
            )

            dispatcher = _build_dispatcher(dispatcher_name, manifest, override)
            conductor = Conductor(
                arbitrator=arb,
                dispatcher=dispatcher,
                team_lead=None,
                session_id=session_id,
                max_steps=500,
            )

            await asyncio.gather(
                conductor.run_roadmap(
                    [WhatsNextSpecialty()], realize_primitive=realizer
                ),
                _bridge_gate_questions(arb, session_id, team_id, io),
            )

            messages = await arb.list_messages(session_id, team_id=team_id)
            final = messages[-1].body if messages else ""
            if final:
                await io.emit("text", {"text": final})
            await io.emit("result", {"stop_reason": "end_turn"})
        finally:
            await arb.close()

    return runner


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
    runner = _make_conductor_runner(
        manifest, dispatcher_name, db_path, team_name, interview
    )
    session = InProcessSession(runner)
    return asyncio.run(
        run_cli(session, team=team_name, prompt="run")
    )


def cmd_rollcall(
    teams_root: Path,
    team: str | None,
    output_format: str,
    timeout: float,
) -> int:
    """Live roll-call: stream each role's real response through the
    integration surface, one role at a time — as if the team were
    standing in a group taking turns."""
    import shutil
    import time as _time

    from services.integration_surface import InProcessSession
    from services.rollcall import (
        ROLL_CALL_PROMPT,
        RollCallError,
        RollCallResult,
        discover_team,
        discover_teams,
        render_json,
        render_table,
    )

    claude_bin = shutil.which("claude")
    if claude_bin is None:
        print("atp: `claude` CLI not found on PATH", file=sys.stderr)
        return 2

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

    def _streaming_claude_runner(claude_bin: str):
        """TeamRunner that shells to `claude --output-format stream-json`
        and emits one `text` event per assistant-message delta. All
        claude-specific parsing lives here; clients consume plain
        protocol events."""
        async def _runner(io, user_turn, ctx):
            await io.emit("state", {"phase": "starting"})
            proc = await asyncio.create_subprocess_exec(
                claude_bin,
                "--model", "haiku",
                "--output-format", "stream-json",
                "--verbose",
                "-p", user_turn,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            assert proc.stdout is not None
            async for raw in proc.stdout:
                try:
                    msg = json.loads(raw.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                if msg.get("type") == "assistant":
                    for block in msg.get("message", {}).get("content", []):
                        if block.get("type") == "text":
                            delta = block.get("text", "")
                            if delta:
                                await io.emit("text", {"text": delta})
            rc = await proc.wait()
            if rc != 0:
                assert proc.stderr is not None
                err = (await proc.stderr.read()).decode(
                    "utf-8", errors="replace"
                )
                await io.emit(
                    "error",
                    {"kind": "subprocess",
                     "message": f"claude exit {rc}: {err[-200:]}",
                     "retryable": False},
                )
                return
            await io.emit("result", {"stop_reason": "end_turn"})

        return _runner

    runner = _streaming_claude_runner(claude_bin)

    async def _run_one(role) -> RollCallResult:
        """Start a session, stream deltas to stdout live, and collect a
        RollCallResult for the final summary."""
        session = InProcessSession(runner)
        parts: list[str] = []
        err: RollCallError | None = None
        t0 = _time.monotonic()
        handle = await session.start(
            team=role.team, prompt=ROLL_CALL_PROMPT,
        )
        try:
            async def _consume():
                async for ev in session.events(handle.session_id):
                    if ev.type == "text":
                        delta = ev.payload.get("text", "")
                        if delta:
                            parts.append(delta)
                            sys.stdout.write(delta)
                            sys.stdout.flush()
                    elif ev.type == "error":
                        raise RuntimeError(
                            ev.payload.get("message", "error event")
                        )
                    elif ev.type == "result":
                        return

            await asyncio.wait_for(_consume(), timeout=timeout)
        except asyncio.TimeoutError:
            err = RollCallError(kind="timeout", message=f">{timeout}s")
        except Exception as exc:
            err = RollCallError(kind="error", message=str(exc))
        finally:
            try:
                await session.close(handle.session_id)
            except Exception:
                pass
        return RollCallResult(
            role=role,
            response="".join(parts),
            duration_ms=int((_time.monotonic() - t0) * 1000),
            error=err,
        )

    async def _run_all() -> list[RollCallResult]:
        results: list[RollCallResult] = []
        bar = "-" * 72
        for i, role in enumerate(roles, 1):
            sys.stdout.write(
                f"\n[{i}/{len(roles)}] {role.kind} :: "
                f"{role.team}/{role.name}\n{bar}\n"
            )
            sys.stdout.flush()
            result = await _run_one(role)
            if result.error is not None:
                sys.stdout.write(
                    f"\n[error] {result.error.kind}: "
                    f"{result.error.message}\n"
                )
            sys.stdout.write(f"\n└── ({result.duration_ms} ms)\n")
            sys.stdout.flush()
            results.append(result)
        return results

    sys.stdout.write(
        f"rollcall: {len(roles)} roles, live via InProcessSession.events()\n"
    )
    sys.stdout.flush()
    results = asyncio.run(_run_all())

    sys.stdout.write("\n")
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
        help=(
            "Live roll-call: stream each role's real response through "
            "the integration surface, one role at a time."
        ),
    )
    p_roll.add_argument("team", nargs="?", default=None)
    p_roll.add_argument(
        "--format", choices=["table", "json"], default="table"
    )
    p_roll.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Per-role timeout in seconds (default 120).",
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
            teams_root, args.team, args.format, args.timeout,
        )

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
