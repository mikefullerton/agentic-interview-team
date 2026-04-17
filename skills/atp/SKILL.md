---
name: atp
version: 0.1.0
description: Agentic Team Pipeline — runs workflows (interview, analyze) against a team directory. Discovery roots, subcommands, and team-loader are follow-up work; this skeleton reserves the skill path and name.
argument-hint: <subcommand> [team] — skeleton only; subcommands not yet implemented
---

# atp v0.1.0

## Status

Skeleton. This skill is reserved for the agentic team pipeline runtime defined in the plan at `~/.claude/plans/let-talk-about-the-cozy-rabin.md`. Subcommands, team discovery (`./teams/`, `~/.agentic-teams/`, `~/.claude/plugins/cache/`), and the `required_atp_version` gate are follow-up work.

## Startup

If `$ARGUMENTS` is `--version`, print `atp v0.1.0` and stop.

Otherwise, print:

```
atp v0.1.0 — skeleton only. Subcommands and team discovery are not yet implemented. See ~/.claude/plans/let-talk-about-the-cozy-rabin.md for the design.
```

Then stop.
