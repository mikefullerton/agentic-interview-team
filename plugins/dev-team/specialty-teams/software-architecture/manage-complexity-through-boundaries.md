---
name: manage-complexity-through-boundaries
description: Define ports (interfaces) describing what the application needs; use adapters to translate between external technologies...
artifact: principles/manage-complexity-through-boundaries.md
version: 1.0.0
---

## Worker Focus
Define ports (interfaces) describing what the application needs; use adapters to translate between external technologies and ports; test core application without databases, UIs, or networks; subsystems evolve independently behind their boundary

## Verify
Core business logic has no imports of UI, database, or network frameworks; adapters implement port interfaces; core can be unit-tested without infrastructure; at least one integration test verifies adapter-to-port wiring
