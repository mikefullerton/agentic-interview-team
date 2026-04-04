---
name: fail-fast
description: Invalid state detected and surfaced immediately at the point of origin; assertions and preconditions in debug builds; in...
artifact: principles/fail-fast.md
version: 1.0.0
---

## Worker Focus
Invalid state detected and surfaced immediately at the point of origin; assertions and preconditions in debug builds; input validation at system boundaries; typed errors returned rather than swallowed; no empty catch blocks; fail gracefully with clear messages in production, loudly in debug

## Verify
No empty catch blocks; typed error returns at system boundaries; debug builds use assertions/preconditions; no silent swallowing of exceptions; production error paths produce user-visible messages
