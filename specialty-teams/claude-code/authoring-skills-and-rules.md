---
name: authoring-skills-and-rules
description: Skill design rules — check inventory first, version from day one, session version check, use `$ARGUMENTS` and `${CLAUDE_...
artifact: guidelines/skills-and-agents/authoring-skills-and-rules.md
version: 1.0.0
---

## Worker Focus
Skill design rules — check inventory first, version from day one, session version check, use `$ARGUMENTS` and `${CLAUDE_SKILL_DIR}`, description under 200 chars, atomic permission prompt, error handling; Rule design rules — imperative tone (MUST/MUST NOT), explicit file paths, single concern, MUST NOT section required, enforcement mechanism, deterministic instructions; Agent design — scope tool access, set maxTurns, clear system prompt

## Verify
Skill has `version` in frontmatter and prints it on invocation; skill description under 200 chars; rule uses RFC 2119 keywords; rule lists explicit file paths for all references; agent has `maxTurns` set; `/lint-skill`, `/lint-rule`, or `/lint-agent` run after every change
