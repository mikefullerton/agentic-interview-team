---

id: fe0daac0-1ba7-4c93-a47e-e42e75612cf6
title: "Skill Structure Reference"
domain: agentic-cookbook://guidelines/implementing/skills-and-agents/skill-structure-reference
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-02
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Reference for Claude Code skill directory layout, frontmatter fields, string substitutions, and invocation control"
platforms: []
tags:
  - skills
  - structure
  - reference
  - frontmatter
depends-on: []
related:
  - agentic-cookbook://guidelines/skills-and-agents/authoring-skills-and-rules
  - agentic-cookbook://guidelines/skills-and-agents/skill-checklist
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - skill-authoring
---

# Skill Structure Reference

> Source: https://code.claude.com/docs/en/skills

## Directory Layout

```
.claude/skills/<skill-name>/
  SKILL.md              # Required — main skill definition
  references/           # Optional — templates, guides, examples
  scripts/              # Optional — helper scripts
  examples/             # Optional — example inputs/outputs
```

## Frontmatter Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| `name` | string | directory name | Display name and slash-command trigger (kebab-case, lowercase, ≤64 chars) |
| `description` | string | — | When to use this skill; shown in context for auto-invocation matching |
| `argument-hint` | string | — | Hint for expected arguments (e.g., `<path>`, `<issue-number>`) |
| `disable-model-invocation` | boolean | `false` | If `true`, Claude will not auto-invoke; user must use `/name` |
| `user-invocable` | boolean | `true` | If `false`, skill is hidden from slash-command menu (background knowledge only) |
| `allowed-tools` | list | all tools | Restrict which tools the skill can use |
| `model` | string | session model | Override the model for this skill |
| `effort` | string | session effort | Override effort level |
| `context` | string | — | Set to `fork` to run in an isolated subagent context |
| `agent` | string | — | Specify subagent type when using `context: fork` |
| `hooks` | object | — | Lifecycle hooks (preInvoke, postInvoke) |
| `paths` | list | — | Glob patterns limiting auto-activation to matching file paths |
| `shell` | string | `bash` | Shell for inline commands (`bash` or `powershell`) |

## String Substitutions

| Variable | Expands to |
|----------|-----------|
| `$ARGUMENTS` | Full argument string passed after `/skill-name` |
| `$0`, `$1`, ... `$N` | Positional arguments (0-based, space-separated) |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_SKILL_DIR}` | Absolute path to this skill's directory |

## Invocation Control Matrix

| `disable-model-invocation` | `user-invocable` | Behavior |
|---------------------------|-----------------|----------|
| `false` (default) | `true` (default) | Auto-invoked by Claude + available as `/command` |
| `true` | `true` | Only via `/command` — never auto-invoked |
| `false` | `false` | Auto-invoked as background knowledge — not in menu |
| `true` | `false` | Never invoked — effectively disabled |

## Skill Locations (Priority Order)

1. Enterprise managed skills (highest priority)
2. Personal skills: `~/.claude/skills/`
3. Project skills: `.claude/skills/`
4. Plugin skills (lowest priority)

## Content Types

- **Reference content**: Background knowledge, conventions, style guides. Runs inline. Use `user-invocable: false` if it should only load automatically.
- **Task content**: Step-by-step instructions for specific actions. Use `disable-model-invocation: true` for side-effect operations.

## Key Guidelines

- Keep SKILL.md under 500 lines; put detailed content in references/
- Use `${CLAUDE_SKILL_DIR}` to reference supporting files
- Description should use keywords users would naturally say
- Skill descriptions are loaded into context to help Claude decide what's available
- Full skill content only loads when invoked
- The main file MUST be named `SKILL.md` (uppercase stem) — Claude Code looks for this exact filename
- Supporting files in references/, scripts/, examples/ should use lowercase descriptive names

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-28 | Mike Fullerton | Initial creation |
