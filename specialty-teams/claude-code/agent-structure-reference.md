---
name: agent-structure-reference
description: Agents are `.md` files in `.claude/agents/` with YAML frontmatter; body is the system prompt; frontmatter fields (name, ...
artifact: guidelines/skills-and-agents/agent-structure-reference.md
version: 1.0.0
---

## Worker Focus
Agents are `.md` files in `.claude/agents/` with YAML frontmatter; body is the system prompt; frontmatter fields (name, description, tools, disallowedTools, model, permissionMode, maxTurns, skills, mcpServers, hooks, memory, background, effort, isolation); tool access via allowlist (`tools`) or denylist (`disallowedTools`), mutually exclusive

## Verify
Agent file in `.claude/agents/`; only recognized frontmatter fields; `tools` and `disallowedTools` not both set; `permissionMode` matches use case; system prompt is focused and unambiguous
