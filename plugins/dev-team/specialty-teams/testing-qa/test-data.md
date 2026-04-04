---
name: test-data
description: Construct test data per test; avoid large shared fixture files; use builder pattern or factory functions for complex obj...
artifact: guidelines/testing/test-data.md
version: 1.0.0
---

## Worker Focus
Construct test data per test; avoid large shared fixture files; use builder pattern or factory functions for complex objects; property-based generators for comprehensive input coverage; inline literals for simple cases; no hidden "magic" fixtures

## Verify
No single shared fixture file used across many unrelated tests; complex object construction uses builders or factories; test data is visible in the test body, not loaded from an opaque external file
