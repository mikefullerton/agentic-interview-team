---
name: skill-structure-reference
description: Directory layout (`.claude/skills/<name>/SKILL.md` + optional references/scripts/examples/); frontmatter fields (name, d...
artifact: guidelines/skills-and-agents/skill-structure-reference.md
version: 1.0.0
---

## Worker Focus
Directory layout (`.claude/skills/<name>/SKILL.md` + optional references/scripts/examples/); frontmatter fields (name, description, argument-hint, disable-model-invocation, user-invocable, allowed-tools, model, effort, context, hooks, paths, shell); string substitutions (`$ARGUMENTS`, `$0`-`$N`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_SKILL_DIR}`); invocation control matrix

## Verify
Skill directory follows `.claude/skills/<name>/SKILL.md` layout; only recognized frontmatter fields present; `${CLAUDE_SKILL_DIR}` used for supporting file references; `argument-hint` present when `$ARGUMENTS` used
