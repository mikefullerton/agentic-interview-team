---

id: 4b60fa16-a4cc-4376-97c3-e455681bffb6
title: "Unit Test Patterns"
domain: agentic-cookbook://guidelines/testing/unit-test-patterns
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "**Structure — Arrange, Act, Assert (AAA):**"
platforms: []
tags: 
  - testing
  - unit-test-patterns
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - writing-tests
---

# Unit Test Patterns

Structure every unit test as Arrange-Act-Assert with one assertion concept per test, no logic in tests, and no coupling between tests.

**Structure — Arrange, Act, Assert (AAA):**

```
// Arrange — set up preconditions
// Act — call the method under test
// Assert — verify the result
```

**Rules:**
- Each test MUST have one assertion concept (not one `assert` — one logical concept)
- Tests MUST NOT contain logic — no `if`, `for`, `try/catch`, `switch`
- Tests SHOULD target the public API, not internals — tests should survive refactoring
- Each test MUST be independent — arrange its own state, don't rely on other tests

**Naming — use descriptive names that read as specifications:**
- `test_parse_order_with_valid_json_returns_order`
- `ParseOrder_WithMissingField_ThrowsValidationError`
- `"returns empty list when no results match"`

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
