---
name: skill-checklist
description: Structure checks (frontmatter present, name kebab-case ≤64 chars, description present, main file named `SKILL.md`, ≤500 ...
artifact: guidelines/skills-and-agents/skill-checklist.md
version: 1.0.0
---

## Worker Focus
Structure checks (frontmatter present, name kebab-case ≤64 chars, description present, main file named `SKILL.md`, ≤500 lines); content quality (single responsibility, actionable steps, `${CLAUDE_SKILL_DIR}` for file refs, no conflicting instructions); best practices (verification method provided, `disable-model-invocation` for side-effect skills, no kitchen-sink anti-pattern, description under ~200 chars)

## Verify
S01/S03/S04/S13 checks pass (FAIL-severity); B06 (no kitchen-sink) passes; C06 (`${CLAUDE_SKILL_DIR}`) passes; skill passes `/lint-skill` with no FAILs
