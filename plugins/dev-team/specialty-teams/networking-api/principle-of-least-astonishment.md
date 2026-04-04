---
name: principle-of-least-astonishment
description: API and system behavior must match what callers expect; names must deliver exactly what they suggest; side effects must ...
artifact: principles/principle-of-least-astonishment.md
version: 1.0.0
---

## Worker Focus
API and system behavior must match what callers expect; names must deliver exactly what they suggest; side effects must be obvious from the API signature; no surprise mutations on read endpoints, no silent state changes

## Verify
No GET endpoints with side effects; endpoint names accurately describe their behavior; idempotent methods (GET/PUT/DELETE) are actually idempotent; no undocumented implicit state changes
