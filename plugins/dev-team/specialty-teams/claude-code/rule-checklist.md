---
name: rule-checklist
description: Content quality (single responsibility, actionable/specific, no conflicting instructions); rule-specific (imperative ton...
artifact: guidelines/skills-and-agents/rule-checklist.md
version: 1.0.0
---

## Worker Focus
Content quality (single responsibility, actionable/specific, no conflicting instructions); rule-specific (imperative tone throughout, numbered steps if procedural, no vague directives, explicit file refs, MUST NOT section present, deterministic, lowercase kebab-case filename); optimization (under 200 lines/8KB, no duplication across rules, `globs` frontmatter for scoped rules)

## Verify
R04 (no vague directives) passes; R05 (explicit file refs) passes; R06 (no contradictions) passes; R11 (MUST NOT section) present; O01 (under 200 lines) met; file passes `/lint-rule` with no FAILs
