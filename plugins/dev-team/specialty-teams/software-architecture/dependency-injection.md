---
name: dependency-injection
description: Components receive dependencies from outside, not constructed internally; pass services via constructor/initializer para...
artifact: principles/dependency-injection.md
version: 1.0.0
---

## Worker Focus
Components receive dependencies from outside, not constructed internally; pass services via constructor/initializer parameters or protocol properties; use protocol/interface types not concrete types; avoid service locator pattern (hidden global lookup)

## Verify
No `new ConcreteService()` inside a component that uses it; dependencies declared as protocol/interface types in constructor signatures; no service locator or static factory lookups inside components; all dependencies injectable for testing
