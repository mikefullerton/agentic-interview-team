---

id: a3f7c1d2-8e4b-4a9f-b6c3-2d1e0f9a8b7c
title: "Scope discipline"
domain: agentic-cookbook://guidelines/implementing/code-quality/scope-discipline
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-28
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Only modify what was requested. State the goal before starting. Note but do not fix adjacent issues."
platforms: []
tags:
  - scope
  - code-quality
  - discipline
depends-on: []
related:
  - agentic-cookbook://guidelines/code-quality/atomic-commits
  - agentic-cookbook://principles/yagni
  - agentic-cookbook://principles/simplicity
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - code-review
  - new-module
---

# Scope discipline

Every task has a boundary. Stay inside it.

## Before starting

The goal MUST be stated in one sentence. If the request is ambiguous or could be interpreted broadly, ask before assuming broad scope. For multi-repo work, confirm which repository before making changes.

## During work

Only what was requested MUST be modified. If asked to fix a bug, fix that bug — do not refactor surrounding code, add missing tests for unrelated functions, update documentation for other features, or "improve" adjacent components.

If you discover issues outside the stated scope — broken imports, outdated comments, missing error handling — **note them** for the user but MUST NOT fix them. A note like "I noticed X is also broken, want me to fix that separately?" preserves the user's ability to prioritize.

## Recognizing scope creep

Watch for these signals that scope is expanding:
- Modifying files not directly related to the stated goal
- Adding functionality the user didn't ask for
- Refactoring code that works correctly but "could be better"
- Redesigning a component when asked to fix one behavior
- Touching more than the minimum files needed for the change

## Why this matters

Unbounded scope leads to:
- Changes the user didn't expect or want, requiring reverts
- Compound bugs from modifying working code alongside new work
- Longer review cycles because the diff includes unrelated changes
- Loss of trust — the user can't predict what will change

Small, focused changes are easier to review, easier to revert, and easier to understand.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-28 | Mike Fullerton | Initial creation |
