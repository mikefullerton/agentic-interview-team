---
id: D931B5B1-F54F-46F1-894F-420957C6D2AE
title: "Best Practices Compliance"
domain: agentic-cookbook://compliance/best-practices
type: compliance
version: 1.0.0
status: draft
language: en
created: 2026-03-28
modified: 2026-03-28
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Compliance checks for testing, code quality, error handling, and separation of concerns."
platforms: []
tags: [compliance, best-practices]
depends-on: []
related:
  - agentic-cookbook://compliance/security
  - agentic-cookbook://compliance/reliability
  - agentic-cookbook://compliance/performance
references: []
---

# Best Practices Compliance

Best practices compliance covers the engineering fundamentals that keep codebases healthy and maintainable — testing strategy, code quality, error handling, and architectural separation. These checks apply broadly to any recipe that produces or modifies code.

## Applicability

This category applies to any recipe or guideline that defines, generates, or modifies source code. If a recipe produces implementation artifacts, these checks govern how that code is tested, structured, and maintained.

## Checks

### unit-test-coverage

Business logic MUST have unit tests with meaningful assertions.

**Applies when:** recipe implements business logic or utility functions.

**Guidelines:**
- [Testing](agentic-cookbook://guidelines/testing/testing)
- [Unit Test Patterns](agentic-cookbook://guidelines/testing/unit-test-patterns)

---

### test-pyramid

Test distribution SHOULD follow the test pyramid (many unit, fewer integration, fewest E2E).

**Applies when:** recipe defines a test strategy or test suite.

**Guidelines:**
- [Test Pyramid](agentic-cookbook://guidelines/testing/test-pyramid)

---

### atomic-commits

Changes MUST be committed atomically — one logical change per commit.

**Applies when:** recipe describes a development workflow or commit strategy.

**Guidelines:**
- [Atomic Commits](agentic-cookbook://guidelines/code-quality/atomic-commits)

---

### code-linting

Code MUST pass configured linting rules without suppression.

**Applies when:** recipe produces source code in any language.

**Guidelines:**
- [Linting](agentic-cookbook://guidelines/code-quality/linting)

---

### post-generation-verification

AI-generated code MUST pass build, test, lint, and log verification before acceptance.

**Applies when:** recipe involves AI-assisted code generation.

**Guidelines:**
- [Post-Generation Verification](agentic-cookbook://guidelines/testing/post-generation-verification)

---

### explicit-error-handling

Errors MUST be handled explicitly; MUST NOT be silently swallowed.

**Applies when:** recipe includes error paths, exception handling, or Result/Optional unwrapping.

**Guidelines:**
- [Fail Fast](agentic-cookbook://principles/fail-fast) (principle)

---

### separation-of-concerns

Business logic MUST be separated from presentation and infrastructure.

**Applies when:** recipe spans multiple architectural layers (UI, domain, data).

**Guidelines:**
- [Separation of Concerns](agentic-cookbook://principles/separation-of-concerns) (principle)

---

### good-test-properties

Tests MUST be fast, isolated, repeatable, and self-validating.

**Applies when:** recipe defines or includes test implementations.

**Guidelines:**
- [Properties of Good Tests](agentic-cookbook://guidelines/testing/properties-of-good-tests)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-28 | Mike Fullerton | Initial creation |
