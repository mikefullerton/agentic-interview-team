---
name: performance
description: Three principles — (1) shell scripts for deterministic work (scaffolding, git, build, lint, file manipulation, metrics);...
artifact: guidelines/skills-and-agents/performance.md
version: 1.0.0
---

## Worker Focus
Three principles — (1) shell scripts for deterministic work (scaffolding, git, build, lint, file manipulation, metrics); (2) model selection tradeoffs (measure token efficiency and latency before downgrading — ask user when unclear); (3) progressive disclosure — rules/CLAUDE.md are per-turn cost, on-demand reads are per-session, target tier-1 under 200 lines/8KB

## Verify
Deterministic steps extracted to shell scripts rather than model reasoning; rule files under 200 lines; CLAUDE.md contains pointers not full procedures; no guideline content front-loaded into every skill step; model downgrade decisions measured, not assumed
