# Testing & QA Specialist

## Domain Coverage
Test pyramid, isolation, determinism, unit test patterns (AAA), behavioral testing, flaky prevention, test data construction, coverage strategy.

## Cookbook Sources
- `cookbook/guidelines/testing/` (12+ guidelines)

## Structured Questions

1. How are your tests distributed? What percentage unit, integration, E2E? If not roughly 80/15/5, why not?

2. Pick a feature — can you test the core logic without a database, UI, or network call?

3. You discovered a production bug. Did you write a reproducing test before fixing it? Will it catch a regression?

4. Describe your most flaky test. What makes it flaky? Fixed or living with it?

5. Your test suite takes 20 minutes. How much is unit vs. integration/E2E? What would you do to get it to 3 minutes?

6. Testing a function that makes a network request — mock the client, stub the response, or hit staging? How do you ensure determinism?

7. Your app serializes/deserializes objects. Do you test the round-trip?

8. Testing a form with validation — each rule independently, or as part of full submission? How many test cases?

9. Tell me about test data. Shared fixtures, builders, or inline literals? Where is test data defined?

10. Testing time-dependent behavior — how do you avoid timing dependencies? Can you test midnight behavior without waiting?

11. A UI test flakes intermittently. Walk me through your debugging process.

12. Testing filesystem reads — real files or mocked I/O? Where stored? How cleaned up?

13. Testing cache behavior — can you test hit vs. miss? Cache invalidation?

14. Testing error handling — what error scenarios do you cover? Timeouts? Invalid responses? Partial failures?

15. Describe the setup for your most complex test. How many lines in the Arrange phase? Is that a red flag?

## Exploratory Prompts

1. If you could only test 10% of your code, which 10% and why? What does that tell you about where risk actually is?

2. If a test fails three months later because requirements changed, is it valuable or noise?

3. If tests were free and instant, how would your strategy change? What would you test that you currently skip?

4. If you had to rewrite your test suite, what would you keep and throw away?
