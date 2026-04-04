---
name: rule-structure-reference
description: Rules are plain `.md` files (no required frontmatter schema), lowercase kebab-case filename, per-turn cost model (rules ...
artifact: guidelines/skills-and-agents/rule-structure-reference.md
version: 1.0.0
---

## Worker Focus
Rules are plain `.md` files (no required frontmatter schema), lowercase kebab-case filename, per-turn cost model (rules in `.claude/rules/` injected every turn); quality criteria — imperative tone, deterministic, explicit file refs, no vague directives; optimization — under 200 lines/8KB, inline small content, reference large, `globs` frontmatter for scoped rules

## Verify
Rule filename is lowercase kebab-case; no uppercase stem unless identity file; per-turn cost reviewed (size ×turns = budget impact); large reference material moved to on-demand reads
