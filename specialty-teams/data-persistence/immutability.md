---
name: immutability
description: Mutable shared state eliminated as the root cause of concurrency bugs; `let`/`val`/`const` used by default; value types ...
artifact: principles/immutability-by-default.md
version: 1.0.0
---

## Worker Focus
Mutable shared state eliminated as the root cause of concurrency bugs; `let`/`val`/`const` used by default; value types (structs, data classes) preferred over reference types; mutation contained behind clear boundaries (actors, StateFlow, useState)

## Verify
No `var`/`var` declarations where `let`/`val` would suffice; mutable state confined to a single owner (actor, ViewModel, store); no shared mutable state across concurrent contexts; data classes or structs used for domain models
