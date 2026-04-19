---

id: dccc22a6-94f3-4cfc-8b30-bae18c56f6f0
title: "Authoring Skills and Rules"
domain: agentic-cookbook://guidelines/implementing/skills-and-agents/authoring-skills-and-rules
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-28
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Best practices for creating Claude Code skills, agents, and rule files."
platforms: []
tags:
  - skills
  - agents
  - rules
  - authoring
  - best-practices
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - skill-authoring
---

# Authoring Skills and Rules

Design skills as single-purpose, versioned extensions. Keep rules minimal, deterministic, and side-effect-free. Check the inventory before creating anything new.

## Overview

This guideline captures lessons learned from building the agentic cookbook's own skills, agents, and rules. It covers design principles, structural conventions, and common pitfalls for each extension type. Follow these practices to produce extensions that are consistent, maintainable, and predictable across sessions.

## Skill Design

1. **Check the inventory first** -- Read the skills table in CLAUDE.md before creating a new skill. Do not duplicate an existing skill's purpose. If the skill is not already listed, confirm the name and purpose with the user before proceeding.

2. **Version from day one** -- Every skill MUST have a `version` field in its frontmatter, support a `--version` parameter, and print its version on every invocation. Increment the version on every change following semver: patch for fixes, minor for new behavior, major for breaking changes.

3. **Session version check** -- The skill MUST read its on-disk version during startup and compare it to the version loaded into the current session. If the versions differ, warn the user that the loaded skill may be stale. Continue running -- do not block execution.

4. **Use `$ARGUMENTS`** -- Do not describe argument handling in prose. Use `$ARGUMENTS`, `$0`, `$1` for input. If the `argument-hint` frontmatter field is declared, the skill body MUST reference these variables.

5. **Use `${CLAUDE_SKILL_DIR}`** -- Reference the skill's own supporting files with `${CLAUDE_SKILL_DIR}`. Use repo-relative paths or `../agentic-cookbook/` paths for cookbook content.

6. **Description under 200 characters** -- The skill description is loaded into every session's context window. Keep it short and include natural trigger keywords so the model invokes the skill when appropriate.

7. **Atomic permission prompt** -- Before any file modifications, present a single yes/no prompt listing every file to be written and every command to be run, with reasons. See `rules/permissions.md` for the full protocol.

8. **Error handling** -- Check prerequisites before starting work. If required files are missing or the environment is misconfigured, stop immediately with a useful error message. Handle invalid arguments explicitly rather than failing silently.

9. **Include a Usage section** -- Every skill MUST include at least one example invocation showing the command and what to expect from the output.

10. **`disable-model-invocation` carefully** -- Use this frontmatter flag for skills that SHOULD only be invoked explicitly by the user. Do NOT set it on skills that other skills need to call via the Skill tool.

11. **No `context: fork` on chainable skills** -- Forked skills cannot invoke other skills or write files visible to the caller. Only use `context: fork` for isolated, read-heavy tasks that return a report.

12. **Don't duplicate between body and references** -- Maintain one authoritative source. Either the skill's markdown body is authoritative and references are supporting material, or vice versa. Never have both with overlapping content that can drift out of sync.

13. **Always lint after creating or modifying** -- Run `/lint-skill <path>` after every change. Fix all FAILs before considering the skill complete. Present WARNs to the user for review.

14. **Update CLAUDE.md and README.md** -- After creating a skill, add it to the skills table in both files. A skill that is not in the inventory is invisible to other sessions.

## Rule Design

1. **Imperative tone throughout** -- Use MUST, MUST NOT, SHOULD, MAY (RFC 2119) consistently. Rules are not advisory or suggestive -- they are directives.

2. **Explicit file paths** -- If the rule instructs the LLM to "read the principles" or "check the guidelines," list every file path it needs to read. An LLM following the rule MUST NOT have to search for referenced content.

3. **Single concern per rule** -- Each rule addresses one topic: planning, implementing, permissions, versioning, committing, etc. Do not combine unrelated concerns into a single rule file.

4. **MUST NOT section required** -- Every rule MUST include a dedicated section listing what the LLM must not do. This section captures anti-patterns, common mistakes, and behaviors that have caused problems in practice.

5. **Enforcement mechanism** -- Do not just state "do X." Include verification steps that confirm X was actually done. For example: "Before proceeding to the next step, confirm that the file was created and contains the expected content."

6. **Deterministic instructions** -- Avoid subjective language like "appropriate," "as needed," or "if it makes sense." Be specific enough that two independent sessions following the rule produce consistent, comparable results.

7. **Same-selection = repair** -- When a user re-selects the current configuration (e.g., re-runs a setup skill with the same parameters), re-apply everything from scratch. Do not skip steps with "already done" -- treat it as a repair operation.

8. **Named requirements, not numbered** -- Use descriptive kebab-case names for requirements, not sequential identifiers like REQ-001. Named requirements make cross-referencing meaningful and survive reordering.

9. **Always lint after creating or modifying** -- Run `/lint-rule <path>` after every change. Fix all FAILs before considering the rule complete. Present WARNs to the user for review.

## Agent Design

Agent authoring is less mature than skill and rule authoring. The following practices reflect early lessons.

1. **Scope tool access** -- Use the `tools` or `disallowedTools` frontmatter fields to restrict what the agent can do. An agent that can do everything is an agent that will eventually do something unexpected.

2. **Set `maxTurns`** -- Prevent unbounded execution by setting a turn limit appropriate to the task complexity. Simple review tasks might need 5-10 turns; complex analysis might need 20-30.

3. **Clear system prompt** -- The markdown body IS the agent's instruction set. Make the instructions focused, unambiguous, and structured. A vague system prompt produces vague results.

4. **Always lint** -- Run `/lint-agent <path>` after creating or modifying an agent. Fix all FAILs.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-28 | Mike Fullerton | Initial creation from lessons learned building cookbook skills |
