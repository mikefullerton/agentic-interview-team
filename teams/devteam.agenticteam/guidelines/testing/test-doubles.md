---

id: eec76082-a68b-4a2b-8f02-5ea3bfdc0a76
title: "Test Doubles"
domain: agentic-cookbook://guidelines/testing/test-doubles
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Use [Martin Fowler's taxonomy](https://martinfowler.com/bliki/TestDouble.html):"
platforms: 
  - csharp
  - kotlin
  - python
  - swift
  - typescript
  - web
tags: 
  - test-doubles
  - testing
depends-on: []
related: []
references: 
  - https://github.com/apple/swift-testing
  - https://github.com/cashapp/turbine
  - https://github.com/pytest-dev/pytest-mock
  - https://martinfowler.com/bliki/TestDouble.html
  - https://mockk.io/
  - https://nsubstitute.github.io/
  - https://vitest.dev/guide/mocking.html
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - writing-tests
---

# Test Doubles

Use [Martin Fowler's taxonomy](https://martinfowler.com/bliki/TestDouble.html):

| Double | Purpose | Example |
|--------|---------|---------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| **Dummy** | Fill a parameter, never used | `null` or empty object |
| **Stub** | Return canned answers | `stub.getUser() → User("test")` |
| **Spy** | Record calls for later verification | `spy.wasCalled("save")` |
| **Mock** | Verify expected interactions | `mock.verify(save, times: 1)` |
| **Fake** | Working implementation, simplified | In-memory database |

**Fakes SHOULD be preferred over mocks** when possible. Fakes exercise real behavior; mocks only verify
expectations. A fake in-memory database catches more bugs than a mock that returns canned SQL results.

**You MUST NOT mock what you don't own.** Wrap external dependencies (HTTP clients, databases, SDKs)
behind your own interface. Mock your interface, not the third-party API directly. This
insulates tests from upstream API changes.

**Platform tools:**
- **Python:** `unittest.mock` (stdlib), [pytest-mock](https://github.com/pytest-dev/pytest-mock)
- **TypeScript/JS:** `jest.mock`, [vitest mocking](https://vitest.dev/guide/mocking.html)
- **Swift:** Protocol conformances (no framework needed), [swift-testing](https://github.com/apple/swift-testing)
- **.NET:** [NSubstitute](https://nsubstitute.github.io/)
- **Kotlin:** [MockK](https://mockk.io/), [Turbine](https://github.com/cashapp/turbine) for Flow testing

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
