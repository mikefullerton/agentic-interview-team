---

id: 8b9def90-2153-45ba-9dcc-fa2aa3bf745e
title: "Agent Structure Reference"
domain: agentic-cookbook://guidelines/implementing/skills-and-agents/agent-structure-reference
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-02
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Reference for Claude Code agent file format, frontmatter fields, tool access patterns, and permission modes"
platforms: []
tags:
  - agents
  - structure
  - reference
  - frontmatter
depends-on: []
related:
  - agentic-cookbook://guidelines/skills-and-agents/authoring-skills-and-rules
  - agentic-cookbook://guidelines/skills-and-agents/agent-checklist
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - skill-authoring
---

# Agent Structure Reference

> Source: https://code.claude.com/docs/en/sub-agents

## File Format

Agents are markdown files with YAML frontmatter, placed in `.claude/agents/`.

```
.claude/agents/<agent-name>.md
```

The markdown body serves as the agent's system prompt.

The filename MUST be lowercase kebab-case (e.g., `build-runner.md`). Uppercase stems are reserved for identity files like `SKILL.md` and `CLAUDE.md`.

## Frontmatter Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| `name` | string | filename | Display name for the agent |
| `description` | string | — | When to use this agent; helps Claude select the right agent |
| `tools` | list | all tools | Allowlist of tools the agent can use |
| `disallowedTools` | list | none | Denylist of tools (mutually exclusive with `tools`) |
| `model` | string | parent model | Override the model for this agent |
| `permissionMode` | string | inherit | `plan` (read-only), `bypassPermissions` (no prompts), or inherit from parent |
| `maxTurns` | number | unlimited | Maximum turns before the agent stops |
| `skills` | list | none | Skills preloaded into the agent's context |
| `mcpServers` | list | none | MCP servers available to the agent |
| `hooks` | object | — | Lifecycle hooks |
| `memory` | string | — | Memory scope for the agent |
| `background` | boolean | `false` | Whether the agent runs in the background |
| `effort` | string | inherit | Override effort level |
| `isolation` | string | — | Set to `worktree` for git worktree isolation |

## Agent Locations (Priority Order)

1. CLI flag (`--agent`)
2. Project agents: `.claude/agents/`
3. Personal agents: `~/.claude/agents/`
4. Plugin agents

## Tool Access Patterns

- **Unrestricted**: Omit both `tools` and `disallowedTools` — agent has access to all tools
- **Allowlist**: Set `tools` to a specific list — agent can ONLY use those tools
- **Denylist**: Set `disallowedTools` — agent can use everything EXCEPT those tools
- `tools` and `disallowedTools` MUST NOT be used together (mutually exclusive)

## Permission Modes

| Mode | Behavior | Use case |
|------|----------|----------|
| (inherit) | Same as parent session | General-purpose agents |
| `plan` | Read-only, no edits | Research and exploration agents |
| `bypassPermissions` | No user prompts | Fully automated pipelines |

## Key Differences from Skills and Rules

| Aspect | Skill | Agent | Rule |
|--------|-------|-------|------|
| Location | `.claude/skills/` | `.claude/agents/` | `rules/`, `.claude/`, or referenced |
| Format | Directory with `SKILL.md` | Single `.md` file | Single `.md`, plain markdown |
| Execution | Runs in current context (or fork) | Always runs as subagent | Loaded into context passively |
| Context | Shares parent context (unless forked) | Isolated context | Shapes main session |
| Tool access | `allowed-tools` in frontmatter | `tools` / `disallowedTools` | N/A |
| Invocation | Auto or `/command` | Via Agent tool or CLI `--agent` | Passive |
| State | No persistent state | Can have `memory` scope | N/A |

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-28 | Mike Fullerton | Initial creation |
