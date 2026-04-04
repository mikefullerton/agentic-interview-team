---
name: yagni
description: Build skills and agents for today's known requirements; speculative generality in prompts (adding "in case we need it" c...
artifact: principles/yagni.md
version: 1.0.0
---

## Worker Focus
Build skills and agents for today's known requirements; speculative generality in prompts (adding "in case we need it" context, future-proofing flags, unused parameters) adds maintenance cost with no current value; adding capabilities when the need materializes is almost always cheaper than maintaining premature abstractions

## Verify
No unused parameters or frontmatter fields; no "in case we need it" context blocks in skill bodies; no speculative multi-platform handling not required by current targets; skills address actual current workflows, not hypothetical future ones
