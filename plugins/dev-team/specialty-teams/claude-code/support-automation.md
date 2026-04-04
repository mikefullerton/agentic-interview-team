---
name: support-automation
description: Skills and agents should expose capabilities through scriptable interfaces — not just interactive use; design operations...
artifact: principles/support-automation.md
version: 1.0.0
---

## Worker Focus
Skills and agents should expose capabilities through scriptable interfaces — not just interactive use; design operations as discrete, composable commands that can be invoked programmatically; provide non-interactive entry points (shell scripts, CLI flags, batch modes) so workflows can drive the extension without human intervention

## Verify
Key operations callable non-interactively (no required interactive prompts for automation paths); shell scripts wrap deterministic operations for direct invocation; skills can be chained without requiring human confirmation at each step; outputs are machine-parseable (not just human-readable)
