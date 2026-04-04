---
name: separation-of-concerns
description: Each skill, rule, and agent should have one reason to change; if describing what a skill/rule does requires "and," consi...
artifact: principles/separation-of-concerns.md
version: 1.0.0
---

## Worker Focus
Each skill, rule, and agent should have one reason to change; if describing what a skill/rule does requires "and," consider splitting; applies at every scale — a skill that does planning AND execution AND reporting is three skills

## Verify
Each skill/rule/agent has a single stated purpose; skill description does not contain "and" joining unrelated concerns; workflow steps are separated into distinct agents rather than one agent doing everything
