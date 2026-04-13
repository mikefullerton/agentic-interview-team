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

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"` to keep the graph current
