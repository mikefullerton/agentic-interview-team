# My Agentic Dev Team

A Claude Code plugin for multi-agent product discovery, analysis, and project building. Distributed via the **agentic-cookbook** marketplace.

**Architecture reference**: `docs/architecture.md` — single source of truth for system design, terminology, components, data flow, file map, and configuration.

## Layout

- `plugins/dev-team/` — self-enclosed plugin (agents, specialists, specialty-teams, skills, scripts, services)
- `.claude/` — local Claude Code config (rules, dev skills)
- `docs/` — architecture reference, planning, specs
- `tests/` — contract tests, test harness
- `planning/` — todo tracking

## Local Testing

To test locally: `cd` into this repo and invoke `/dev-team interview`.
