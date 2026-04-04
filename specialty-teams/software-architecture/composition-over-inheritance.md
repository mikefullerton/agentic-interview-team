---
name: composition-over-inheritance
description: Default to composing behaviors from small, focused pieces; use inheritance only for genuine "is-a" relationships and eve...
artifact: principles/composition-over-inheritance.md
version: 1.0.0
---

## Worker Focus
Default to composing behaviors from small, focused pieces; use inheritance only for genuine "is-a" relationships and even then sparingly; prefer protocols/interfaces over base classes; wrap rather than subclass when extending behavior

## Verify
No inheritance hierarchies more than 1 level deep except for genuine is-a relationships; shared behavior achieved via protocol/interface composition not base classes; no subclassing to extend behavior where wrapping is possible
