---
name: atp
version: 0.2.0
description: Agentic Team Pipeline — load a team from teams/<name>/ and drive it through the conductor. Phase-1 subcommands: list, describe, run. Wider discovery roots and richer planning are follow-ups.
argument-hint: <subcommand> [team] — list | describe <team> | run <team> [--dispatcher mock|claude-code] [--db <path>]
---

# atp v0.2.0

## Status

Phase 1 — subcommands wired end-to-end against `teams/devteam/`, `teams/puppynamingteam/`, and `teams/projectteam/`. Roadmap planning agents and wider discovery (`~/.agentic-teams/`, `~/.claude/plugins/cache/`) are follow-up work.

## Startup

If `$ARGUMENTS` is `--version`, print `atp v0.2.0` and stop.

Otherwise, shell out to the CLI with the remaining arguments and stream its output verbatim:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/atp/scripts/atp_cli.py $ARGUMENTS
```

## Subcommands

- `atp list` — print discovered teams in `./teams/`.
- `atp describe <team>` — print a team's manifest (specialists + specialties).
- `atp run <team> [--dispatcher mock|claude-code] [--db <path>]` — build a one-node-per-specialty demo roadmap for the team and run it through the conductor. `--dispatcher mock` uses canned responses; `--dispatcher claude-code` shells out to the real CLI.

The mock dispatcher auto-generates a response for every worker in the team's manifest plus the scheduler pair, so `atp run` always has a complete canned response set regardless of team size.

## Follow-ups

- `atp plan <team>` — drive a real planning conversation to produce a meaningful roadmap (not one-node-per-specialty).
- Discovery beyond `./teams/` — `~/.agentic-teams/`, `~/.claude/plugins/cache/`.
- `required_atp_version` gate on team.md frontmatter.
