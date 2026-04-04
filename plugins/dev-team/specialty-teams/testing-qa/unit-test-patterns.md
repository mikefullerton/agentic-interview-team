---
name: unit-test-patterns
description: AAA structure (Arrange/Act/Assert), one assertion concept per test, no logic in tests (no if/for/try-catch), test the pu...
artifact: guidelines/testing/unit-test-patterns.md
version: 1.0.0
---

## Worker Focus
AAA structure (Arrange/Act/Assert), one assertion concept per test, no logic in tests (no if/for/try-catch), test the public API not internals, each test arranges its own state independently

## Verify
All tests follow AAA; no conditional or loop logic inside test bodies; test names read as specifications (e.g., `ParseOrder_WithMissingField_ThrowsValidationError`); tests do not share mutable state
