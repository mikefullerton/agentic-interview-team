---
name: idempotency
description: User actions and system operations safe to repeat without duplicate side effects; buttons debounced or disabled during a...
artifact: principles/idempotency.md
version: 1.0.0
---

## Worker Focus
User actions and system operations safe to repeat without duplicate side effects; buttons debounced or disabled during async operations; idempotency keys on API calls with side effects; database migrations safe to run multiple times; state transitions check current state before applying

## Verify
Submit buttons disabled or debounced during in-flight requests; idempotency keys present on write API calls; migration scripts use IF NOT EXISTS or equivalent guards; state transition logic reads current state before writing
