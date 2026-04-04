---
name: flaky-test-prevention
description: No shared mutable state between tests, no execution-order dependencies, no real network calls in unit tests, no sleep() ...
artifact: guidelines/testing/flaky-test-prevention.md
version: 1.0.0
---

## Worker Focus
No shared mutable state between tests, no execution-order dependencies, no real network calls in unit tests, no sleep() or timing-dependent assertions, no filesystem side effects in unit tests, inject time as a dependency — intermittent failures treated as P1 bugs

## Verify
No `sleep()` in test bodies; no real HTTP calls in unit tests; no shared class-level mutable fields used across tests; clock/time injected rather than read directly
