---

id: 05d00147-5c49-42d8-bdbd-cf8fd7dc2379
title: "Flaky Test Prevention"
domain: agentic-cookbook://guidelines/testing/flaky-test-prevention
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Flaky tests destroy confidence. Quarantine them immediately — fix or delete, never ignore."
platforms: 
  - typescript
  - web
tags: 
  - flaky-test-prevention
  - testing
depends-on: []
related: []
references: 
  - https://martinfowler.com/articles/nonDeterminism.html
  - https://testing.googleblog.com/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - writing-tests
  - pre-pr
---

# Flaky Test Prevention

Flaky tests destroy confidence. Quarantine them immediately — fix or delete, never ignore.

**Rules:**
- Tests MUST NOT share mutable state (each test arranges its own)
- Tests MUST NOT depend on execution order
- Unit tests MUST NOT make real network calls (use fakes or stubs)
- Tests MUST NOT use `sleep()` or timing-dependent assertions — use deterministic waits or callbacks
- Unit tests MUST NOT produce filesystem side effects (use temp directories, clean up in teardown)
- Tests SHOULD NOT rely on system clock — inject time as a dependency
- If a test fails intermittently, it is broken. It MUST be treated as a P1 bug.

References:
- [Martin Fowler: Eradicating Non-Determinism in Tests](https://martinfowler.com/articles/nonDeterminism.html)
- [Google Testing Blog: Flaky Tests](https://testing.googleblog.com/)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
