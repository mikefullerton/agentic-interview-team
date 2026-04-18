---
name: atp
version: 0.3.0
description: Agentic Team Pipeline — load a team from teams/<name>/ and drive it through the conductor. Subcommands: list, describe, run, rollcall. Wider discovery roots and richer planning are follow-ups.
argument-hint: <subcommand> [team] — list | describe <team> | run <team> [--dispatcher mock|claude-code] [--db <path>] | rollcall [team] [--format table|json]
---

# atp v0.3.0

## Status

Phase 1 — subcommands wired end-to-end against `teams/devteam/`, `teams/puppynamingteam/`, and `teams/projectteam/`. Roadmap planning agents and wider discovery (`~/.agentic-teams/`, `~/.claude/plugins/cache/`) are follow-up work.

## Startup

If `$ARGUMENTS` is `--version`, print `atp v0.3.0` and stop.

Otherwise, shell out to the CLI with the remaining arguments and stream its output verbatim:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/atp/scripts/atp_cli.py $ARGUMENTS
```

## Subcommands

- `atp list` — print discovered teams in `./teams/`.
- `atp describe <team>` — print a team's manifest (specialists + specialties).
- `atp run <team> [--dispatcher mock|claude-code] [--db <path>]` — build a one-node-per-specialty demo roadmap for the team and run it through the conductor. `--dispatcher mock` uses canned responses; `--dispatcher claude-code` shells out to the real CLI.
- `atp rollcall [team] [--format table|json] [--concurrency N] [--timeout S]` — discover every team-lead, specialist-worker, and specialist-verifier under `./teams/` (or under a single `team` if given) and ping each one through the integration surface. Prints a table (default) or one NDJSON line per role. Exit code is `0` if every role responds, `2` if any role errors or times out. v1 uses a scripted in-process runner that proves discovery + integration surface + formatting without an LLM; the real-LLM variant lives under `testing/functional/tests/rollcall/` and is gated by `AGENTIC_REAL_LLM_SMOKE=1`.

The mock dispatcher auto-generates a response for every worker in the team's manifest plus the scheduler pair, so `atp run` always has a complete canned response set regardless of team size.

## Follow-ups

- `atp plan <team>` — drive a real planning conversation to produce a meaningful roadmap (not one-node-per-specialty).
- Discovery beyond `./teams/` — `~/.agentic-teams/`, `~/.claude/plugins/cache/`.
- `required_atp_version` gate on team.md frontmatter.
