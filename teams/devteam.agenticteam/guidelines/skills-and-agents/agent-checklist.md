---

id: ef7e17ea-a4c1-4946-aff7-a81cb27885a0
title: "Agent Lint Checklist"
domain: agentic-cookbook://guidelines/cookbook/skills-and-agents/agent-checklist
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-02
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Comprehensive lint checklist for validating Claude Code agent structure, content quality, and best practices"
platforms: []
tags:
  - agents
  - linting
  - checklist
  - quality
depends-on: []
related:
  - agentic-cookbook://guidelines/skills-and-agents/authoring-skills-and-rules
  - agentic-cookbook://guidelines/skills-and-agents/agent-structure-reference
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - skill-authoring
  - pre-pr
---

# Agent Lint Checklist

> Last updated: 2026-03-27
> Sources:
> - https://code.claude.com/docs/en/sub-agents
> - https://code.claude.com/docs/en/best-practices

Severity levels:
- **FAIL** — violates a hard requirement; MUST fix
- **WARN** — departs from best practice; SHOULD fix
- **INFO** — suggestion for improvement; MAY fix

---

## Structure & Format

| ID  | Criterion | How to check | Severity |
|-----|-----------|-------------|----------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| S01 | YAML frontmatter present | File starts with `---`, has closing `---` | FAIL |
| S02 | `name` field present | Frontmatter contains `name:` | WARN |
| S03 | `name` is kebab-case, lowercase, ≤64 chars | Regex: `^[a-z][a-z0-9-]{0,63}$` | FAIL |
| S04 | `description` field present | Frontmatter contains `description:` | FAIL |
| S05 | Description uses natural trigger keywords | Description includes phrases users would say; not too vague or too narrow | WARN |
| S11 | Correct file location | Agent is in `.claude/agents/` or `~/.claude/agents/` | WARN |
| S12 | Only recognized frontmatter fields | Check against known fields: name, description, tools, disallowedTools, model, permissionMode, maxTurns, skills, mcpServers, hooks, memory, background, effort, isolation | WARN |
| S13 | Filename is lowercase kebab-case | Filename matches `^[a-z][a-z0-9-]*\.md$`; UPPERCASE stems are reserved for identity files like `SKILL.md` and `CLAUDE.md` | WARN |

---

## Content Quality

| ID  | Criterion | How to check | Severity |
|-----|-----------|-------------|----------|
| C01 | Single responsibility | Agent has one clear purpose; not a grab-bag of unrelated tasks | WARN |
| C04 | Error handling covered | System prompt addresses what to do when things go wrong (tool failures, missing files, bad input) | WARN |
| C07 | Instructions are actionable and specific | System prompt tells the agent what to do concretely | WARN |
| C08 | No conflicting instructions | Body does not contradict itself | FAIL |
| C09 | Well-structured markdown | Uses headings, lists, code blocks; not a wall of unstructured text | WARN |

---

## Best Practices

| ID  | Criterion | How to check | Severity |
|-----|-----------|-------------|----------|
| B01 | Verification method provided | Agent includes how to validate it completed successfully | WARN |
| B02 | Does not replicate native capabilities | Agent doesn't teach Claude things it already knows | WARN |
| B05 | Examples or usage patterns included | Body or description includes expected usage context | WARN |
| B06 | No kitchen-sink anti-pattern | Agent doesn't try to do everything — stays focused on its stated purpose | FAIL |
| B07 | No infinite-exploration anti-pattern | Agent scopes its investigation; doesn't read unbounded numbers of files | WARN |
| B08 | Not a CLAUDE.md dump | Agent content is agent-appropriate, not a copy-paste of project rules that belong in CLAUDE.md | WARN |
| B10 | Model override appropriate | If `model:` is set, it matches the agent's complexity | WARN |
| B12 | Description concise for context budget | Description is under ~200 characters to avoid consuming excessive context | WARN |

---

## Agent-Specific

| ID  | Criterion | How to check | Severity |
|-----|-----------|-------------|----------|
| A01 | `name` and `description` frontmatter present | Agent .md file has both fields | FAIL |
| A02 | Tool access appropriately restricted | `tools` or `disallowedTools` limits access for specialized agents | WARN |
| A03 | `model` field specified if beneficial | Agent benefits from a specific model for its task | INFO |
| A04 | System prompt is clear and focused | Markdown body gives the agent a clear role and scope | WARN |
| A05 | `permissionMode` set appropriately | `plan` for read-only agents, `bypassPermissions` for fully automated | WARN |
| A06 | `maxTurns` set for bounded tasks | Simple agents that should finish quickly have a turn limit | WARN |
| A07 | `skills` lists preloaded skills if needed | Agent that needs domain knowledge has relevant skills preloaded | INFO |
| A08 | `memory` scope appropriate | If agent accumulates knowledge, memory is scoped correctly | INFO |

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-28 | Mike Fullerton | Initial creation |
