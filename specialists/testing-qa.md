# Testing & QA Specialist

## Role
Test pyramid distribution, isolation, determinism, unit test patterns, test doubles, property-based testing, flaky prevention, mutation validation, security scanning, and post-generation verification.

## Persona
(coming)

## Cookbook Sources
- `guidelines/testing/` (13 files)

## Specialty Teams

### testing
- **Artifact**: `guidelines/testing/testing.md`
- **Worker focus**: Every change needs tests, every bug fix needs a regression test; prioritize unit tests over integration; test state transitions, edge cases, serialization round-trips; avoid fragile UI tests — test component logic as units instead
- **Verify**: Test file exists for every implementation file; bug fix commits include a regression test; no UI-only tests for logic that can be unit-tested

### test-pyramid
- **Artifact**: `guidelines/testing/test-pyramid.md`
- **Worker focus**: 80% unit / 15% integration / 5% E2E; unit tests are fast and isolated; integration tests use real databases/filesystems/HTTP where practical; E2E reserved for critical user journeys only
- **Verify**: Test count ratios approximate 80/15/5; no E2E test for behavior coverable by unit test; if unit test can't cover behavior, integration test used before escalating to E2E

### unit-test-patterns
- **Artifact**: `guidelines/testing/unit-test-patterns.md`
- **Worker focus**: AAA structure (Arrange/Act/Assert), one assertion concept per test, no logic in tests (no if/for/try-catch), test the public API not internals, each test arranges its own state independently
- **Verify**: All tests follow AAA; no conditional or loop logic inside test bodies; test names read as specifications (e.g., `ParseOrder_WithMissingField_ThrowsValidationError`); tests do not share mutable state

### properties-of-good-tests
- **Artifact**: `guidelines/testing/properties-of-good-tests.md`
- **Worker focus**: Tests should be isolated, composable, deterministic, fast, writable, readable, behavioral (test what not how), structure-insensitive, automated, specific, predictive, and inspiring — Kent Beck's Test Desiderata
- **Verify**: Any test set can run in any order without failure; a failing test identifies exactly one cause; refactoring internals does not break tests; tests run without manual steps

### flaky-test-prevention
- **Artifact**: `guidelines/testing/flaky-test-prevention.md`
- **Worker focus**: No shared mutable state between tests, no execution-order dependencies, no real network calls in unit tests, no sleep() or timing-dependent assertions, no filesystem side effects in unit tests, inject time as a dependency — intermittent failures treated as P1 bugs
- **Verify**: No `sleep()` in test bodies; no real HTTP calls in unit tests; no shared class-level mutable fields used across tests; clock/time injected rather than read directly

### test-doubles
- **Artifact**: `guidelines/testing/test-doubles.md`
- **Worker focus**: Use Martin Fowler's taxonomy (Dummy/Stub/Spy/Mock/Fake); prefer fakes over mocks — fakes exercise real behavior; never mock what you don't own — wrap external dependencies behind your own interface first
- **Verify**: In-memory fakes used for databases/queues where possible; no mocks of third-party APIs directly (only mock your own interface); platform-appropriate mock library used (NSubstitute/.NET, MockK/Kotlin, pytest-mock/Python, vitest/TS)

### test-data
- **Artifact**: `guidelines/testing/test-data.md`
- **Worker focus**: Construct test data per test; avoid large shared fixture files; use builder pattern or factory functions for complex objects; property-based generators for comprehensive input coverage; inline literals for simple cases; no hidden "magic" fixtures
- **Verify**: No single shared fixture file used across many unrelated tests; complex object construction uses builders or factories; test data is visible in the test body, not loaded from an opaque external file

### property-based-testing
- **Artifact**: `guidelines/testing/property-based-testing.md`
- **Worker focus**: Use for parsers, serializers, data transformers, encoders/decoders, validators — anything where "for all valid inputs X, property Y holds"; platform tools: Hypothesis (Python), fast-check (TypeScript), FsCheck (.NET), jqwik (Kotlin/JVM), swift-testing parameterized (Swift)
- **Verify**: At least one property test per data transformation function; round-trip property tested for encode/decode pairs (`encode(decode(x)) == x`); preservation property tested for collection operations

### mutation-testing
- **Artifact**: `guidelines/testing/mutation-testing.md`
- **Worker focus**: Run mutation testing before claiming tests are complete; platform tools: mutmut (Python), Stryker (TypeScript/JS/.NET), Muter (Swift), Pitest (Kotlin/JVM); examine surviving mutants and write additional tests to kill them
- **Verify**: Mutation testing run and results reviewed; no surviving mutants in critical paths; mutation score documented or acceptable threshold met before marking test suite complete

### security-testing
- **Artifact**: `guidelines/testing/security-testing.md`
- **Worker focus**: Run SAST (Semgrep all languages, Bandit for Python, CodeQL for deep analysis), dependency scanning (pip-audit, npm audit, dotnet vulnerable, Snyk), and DAST (OWASP ZAP for running web services) as part of post-generation verification
- **Verify**: `semgrep scan --config=auto .` run with no critical findings; dependency audit command run with no high/critical vulnerabilities; OWASP ZAP scan run against local service if web-facing

### post-generation-verification
- **Artifact**: `guidelines/testing/post-generation-verification.md`
- **Worker focus**: Every generated artifact must pass 6 steps — build (all platforms), test (full suite), lint (platform linter), log verification (grep for expected log messages), accessibility audit (VoiceOver/TalkBack labels, tap targets, contrast), code review against best practices
- **Verify**: Build passes for all target platforms; all tests pass; linter reports no errors; log grep confirms expected output; accessibility tap targets meet minimums (44pt iOS, 48dp Android)

### the-testing-workflow
- **Artifact**: `guidelines/testing/the-testing-workflow.md`
- **Worker focus**: Complete closed-loop workflow — write implementation, write unit tests (with property-based for data transforms), run tests, validate test quality with mutation testing, kill surviving mutants, run security scan, run E2E verification; AI generates tests, deterministic tools validate them, AI closes gaps
- **Verify**: All 7 workflow steps executed in order; mutation testing results reviewed before declaring tests complete; security scan step not skipped; E2E verification covers critical user journeys

## Exploratory Prompts

1. If you could only test 10% of your code, which 10% and why? What does that tell you about where risk actually is?

2. If a test fails three months later because requirements changed, is it valuable or noise?

3. If tests were free and instant, how would your strategy change? What would you test that you currently skip?

4. If you had to rewrite your test suite, what would you keep and throw away?
