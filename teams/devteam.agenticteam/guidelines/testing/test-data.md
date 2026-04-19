---

id: 38969d3a-884a-4d6e-adae-5398464ee0de
title: "Test Data"
domain: agentic-cookbook://guidelines/testing/test-data
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "**Construct what you need, per test.** Large shared fixture files SHOULD be avoided."
platforms: []
tags: 
  - test-data
  - testing
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - writing-tests
  - data-modeling
---

# Test Data

Build test data inline using builders or factories so every test declares exactly what it needs. Avoid shared fixture files and magic data.

**Construct what you need, per test.** Avoid large shared fixture files.

- **Builder pattern** or **factory functions** SHOULD be used for complex objects — each test calls
  `makeOrder(status: .pending)` with only the fields it cares about, defaults for the rest
- **Property-based generators** (Hypothesis strategies, fast-check arbitraries) for
  comprehensive input coverage
- **Inline literals** for simple cases — `assert parse("hello") == "hello"` is clear
- **No magic fixtures** — if a test needs specific data, the data MUST be visible in the test

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
