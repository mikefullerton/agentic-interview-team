---
name: manage-complexity-through-boundaries
description: Well-defined interfaces between subsystems — skills expose clear input/output contracts; agents receive narrow, specific...
artifact: principles/manage-complexity-through-boundaries.md
version: 1.0.0
---

## Worker Focus
Well-defined interfaces between subsystems — skills expose clear input/output contracts; agents receive narrow, specific instructions; use adapters to translate between external systems and internal interfaces; don't let external technology details bleed across boundaries

## Verify
Skill inputs and outputs are clearly documented; agents receive only the context needed for their task (not the full session history); external tool calls wrapped behind a consistent interface rather than scattered inline
