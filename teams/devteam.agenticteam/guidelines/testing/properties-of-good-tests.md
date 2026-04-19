---

id: e5af9ba5-f484-40c3-9738-470090f5241c
title: "Properties of Good Tests"
domain: agentic-cookbook://guidelines/testing/properties-of-good-tests
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "From Kent Beck's Test Desiderata — tests should be:"
platforms: []
tags: 
  - properties-of-good-tests
  - testing
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - writing-tests
  - code-review
---

# Properties of Good Tests

From Kent Beck's Test Desiderata — tests should be:

1. **Isolated** — tests MUST NOT share mutable state or depend on execution order
2. **Composable** — tests MUST be runnable in any subset and any order
3. **Deterministic** — tests MUST produce the same result every time, no flakiness
4. **Fast** — milliseconds per unit test, seconds per integration test
5. **Writable** — easy to author, low ceremony
6. **Readable** — a failing test tells you what broke and why
7. **Behavioral** — tests SHOULD verify what the code does, not how it does it
8. **Structure-insensitive** — refactoring internals SHOULD NOT break tests
9. **Automated** — no manual steps, no human judgment needed
10. **Specific** — a failure points to exactly one cause
11. **Predictive** — passing tests mean the code works in production
12. **Inspiring** — confidence to refactor and ship

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
