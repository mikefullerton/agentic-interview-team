---
name: design-for-deletion
description: Treat every line of code as a maintenance liability; build disposable units that can be thrown away without affecting th...
artifact: principles/design-for-deletion.md
version: 1.0.0
---

## Worker Focus
Treat every line of code as a maintenance liability; build disposable units that can be thrown away without affecting the rest of the system; avoid premature abstraction for reuse; duplicate rather than couple when in doubt

## Verify
No abstractions justified solely by anticipated future reuse; no shared coupling where duplication would be cheaper; modules can be removed without cascading changes
