---

id: 2945503d-8e92-44ca-bc64-20285eb29296
title: "Skill Lint Checklist"
domain: agentic-cookbook://guidelines/cookbook/skills-and-agents/skill-checklist
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-02
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Comprehensive lint checklist for validating Claude Code skill structure, content quality, and best practices"
platforms: []
tags:
  - skills
  - linting
  - checklist
  - quality
depends-on: []
related:
  - agentic-cookbook://guidelines/skills-and-agents/authoring-skills-and-rules
  - agentic-cookbook://guidelines/skills-and-agents/skill-structure-reference
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - skill-authoring
  - pre-pr
---

# Skill Lint Checklist

> Last updated: 2026-03-27
> Sources:
> - https://code.claude.com/docs/en/skills
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
| S05 | Description uses natural trigger keywords | Description includes phrases users would say; not too vague ("does stuff") or too narrow ("only for X on Tuesdays") | WARN |
| S06 | SKILL.md ≤ 500 lines | `wc -l SKILL.md` | WARN |
| S07 | Supporting files in subdirectories | Loose files (non-SKILL.md) at skill root → should be in references/, scripts/, examples/ | WARN |
| S08 | SKILL.md references its supporting files | If references/ exists, SKILL.md mentions those files or uses `${CLAUDE_SKILL_DIR}` to load them | WARN |
| S09 | Directory name matches `name` field | Compare directory basename to frontmatter `name` | WARN |
| S10 | `argument-hint` present if `$ARGUMENTS` used | SKILL.md uses `$ARGUMENTS` or `$1`, `$2` but frontmatter lacks `argument-hint:` | WARN |
| S11 | Correct file location | Skill is in `.claude/skills/` or `~/.claude/skills/` | WARN |
| S12 | Only recognized frontmatter fields | Check against known fields: name, description, argument-hint, disable-model-invocation, user-invocable, allowed-tools, model, effort, context, agent, hooks, paths, shell | WARN |
| S13 | Main file named `SKILL.md` (uppercase stem) | Filename is exactly `SKILL.md`, not `skill.md` or `Skill.md` — Claude Code looks for this exact name | FAIL |
| S14 | Supporting files use lowercase descriptive names | Files in references/, scripts/, examples/ match `^[a-z][a-z0-9-]*(\.[a-z]+)+$`; names describe content (not `doc1.md`) | WARN |

---

## Content Quality

| ID  | Criterion | How to check | Severity |
|-----|-----------|-------------|----------|
| C01 | Single responsibility | Skill has one clear purpose; not a grab-bag of unrelated instructions | WARN |
| C02 | Task skills have step-by-step instructions | If the skill performs actions (not just reference), it should have numbered steps or a clear workflow | WARN |
| C03 | Reference vs task content appropriate | Reference skills (background knowledge) should not have imperative "do X" steps; task skills should not be pure documentation | WARN |
| C04 | Error handling covered | Instructions address what to do when things go wrong (tool failures, missing files, bad input) | WARN |
| C05 | `$ARGUMENTS` used when skill accepts input | Description implies the skill takes input but body never references `$ARGUMENTS` | WARN |
| C06 | `${CLAUDE_SKILL_DIR}` for file references | Skill references its own supporting files using `${CLAUDE_SKILL_DIR}`, not hardcoded paths | FAIL |
| C07 | Instructions are actionable and specific | Steps tell Claude what to do concretely, not vague directives like "handle errors appropriately" | WARN |
| C08 | No conflicting instructions | Body does not contradict itself (e.g., "always do X" then later "never do X") | FAIL |
| C09 | Well-structured markdown | Uses headings, lists, code blocks; not a wall of unstructured text | WARN |
| C10 | No redundancy with supporting files | SKILL.md and reference files don't duplicate large blocks of the same content | WARN |

---

## Best Practices

| ID  | Criterion | How to check | Severity |
|-----|-----------|-------------|----------|
| B01 | Verification method provided | Skill includes how to validate it worked (run tests, check output, verify file exists) | WARN |
| B02 | Does not replicate native capabilities | Skill doesn't teach Claude things it already knows (basic git, standard coding, etc.) | WARN |
| B03 | `disable-model-invocation` for side-effect skills | Skills that deploy, commit, send messages, or modify external state should set `disable-model-invocation: true` | WARN |
| B04 | `context: fork` considered for isolated tasks | Task skills that do heavy reading/fetching and return a result benefit from fork isolation | INFO |
| B05 | Examples or usage patterns included | Skill body or references include at least one example invocation or expected output | WARN |
| B06 | No kitchen-sink anti-pattern | Skill doesn't try to do everything — stays focused on its stated purpose | FAIL |
| B07 | No infinite-exploration anti-pattern | Task skills scope their investigation; don't read unbounded numbers of files | WARN |
| B08 | Not a CLAUDE.md dump | Skill content is skill-appropriate, not a copy-paste of project rules that belong in CLAUDE.md | WARN |
| B09 | `allowed-tools` used if tool restriction needed | If the skill should only use certain tools, `allowed-tools` is set | INFO |
| B10 | Model override appropriate | If `model:` is set, it matches the skill's complexity (don't use opus for trivial tasks) | WARN |
| B11 | Dynamic context injection correct | If `` !`command` `` syntax is used, the command is safe, fast, and deterministic | WARN |
| B12 | Description concise for context budget | Description is under ~200 characters to avoid consuming excessive context | WARN |

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-28 | Mike Fullerton | Initial creation |
