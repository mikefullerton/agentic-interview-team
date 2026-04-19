---
id: 1357be12-5a58-4143-a570-849c114770c5
title: "Separation of concerns"
domain: agentic-cookbook://principles/separation-of-concerns
type: principle
version: 1.0.0
status: accepted
language: en
created: 2026-03-27
modified: 2026-03-27
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "A module should have one reason to change. If describing what a module does requires 'and,' consider splitting. This ..."
platforms: []
tags: 
  - separation-of-concerns
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
---

# Separation of concerns

A module should have one reason to change. If describing what a module does requires "and," consider splitting. This applies at every scale: functions, modules, services, teams.

- Describe each module's responsibility in one sentence without using "and" — if you cannot, split it
- Keep UI rendering, business logic, and data access in separate layers that can change independently
- When a change to one feature forces edits in an unrelated feature, treat it as a coupling defect

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
