---
name: agent-checklist
description: Structure checks (frontmatter present with name+description, kebab-case filename); content quality (single responsibilit...
artifact: guidelines/skills-and-agents/agent-checklist.md
version: 1.0.0
---

## Worker Focus
Structure checks (frontmatter present with name+description, kebab-case filename); content quality (single responsibility, error handling covered, no conflicting instructions); agent-specific (tool access restricted via `tools`/`disallowedTools`, `maxTurns` set for bounded tasks, `permissionMode` appropriate — `plan` for read-only, `bypassPermissions` for automated)

## Verify
A01 (name+description present) passes; A02 (tool access restricted) reviewed; A05 (`permissionMode`) appropriate for task; A06 (`maxTurns`) set; agent passes `/lint-agent` with no FAILs
