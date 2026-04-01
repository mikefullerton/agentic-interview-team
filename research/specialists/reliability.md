# Reliability & Error Handling Specialist

## Domain Coverage
Fail fast, idempotency, error categorization, retry strategies, timeout handling, graceful degradation, state recovery, data integrity, circuit breakers, monitoring.

## Cookbook Sources
- `cookbook/principles/fail-fast.md`
- `cookbook/principles/idempotency.md`
- `cookbook/compliance/reliability.md`

## Structured Questions

1. How will you categorize errors — network, validation, permission, database? Typed errors or generic exceptions? Retryable vs. non-retryable?

2. For network calls, what's your retry strategy? Exponential backoff? How many retries? Different for reads vs. writes?

3. For API calls that create or update data, do you have idempotency keys? How will you store and manage them?

4. What are your default timeouts — API calls, database queries, file I/O? Will the system be in a consistent state after a timeout?

5. When an operation fails, what does the user see? Generic message or specific? Correlation ID for debugging?

6. While a network request is in flight, what happens to the submit button? Race conditions if user clicks multiple times?

7. If your app crashes mid-operation, what state is lost? Can it recover? Payment submitted but confirmation didn't arrive — what happens on restart?

8. If the network goes down, does the app queue operations, show offline message, or fail immediately? Reconciliation when back online?

9. At what layer do you validate data — client, API gateway, business logic, database? Duplicate at each layer?

10. If a database query fails, how do you distinguish "data doesn't exist" vs. "query failed"?

11. If an external API dependency is down, does your entire app fail or degrade gracefully?

12. What metrics will you track — error rates, latency, retry counts, timeouts? How will you be alerted?

13. How will you detect data corruption — checksums, validation rules, periodic integrity checks?

14. If a downstream service repeatedly fails, will you implement a circuit breaker?

## Exploratory Prompts

1. What's the worst thing that could happen silently — a lost transaction, inconsistent state, data that never syncs? How would you catch it?

2. If one component fails, could it cascade? Database gets slow — how does that ripple through?

3. As you grow to 10x users, 100x traffic, which error-handling assumptions break?

4. For your most critical operation, walk me through every failure scenario and how you'd recover.

5. Why validate the same data at both client and server? What failure would you miss if you didn't?
