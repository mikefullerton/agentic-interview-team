# Reliability & Error Handling Specialist

## Role
Fail fast, idempotency, error categorization, retry strategies, timeout handling, graceful degradation, state recovery, data integrity, circuit breakers, monitoring.

## Persona
(coming)

## Cookbook Sources
- `principles/fail-fast.md`
- `principles/idempotency.md`
- `compliance/reliability.md`

## Manifest

- specialty-teams/reliability/fail-fast.md
- specialty-teams/reliability/idempotency.md
- specialty-teams/reliability/reliability-compliance.md

## Exploratory Prompts

1. What's the worst thing that could happen silently — a lost transaction, inconsistent state, data that never syncs? How would you catch it?

2. If one component fails, could it cascade? Database gets slow — how does that ripple through?

3. As you grow to 10x users, 100x traffic, which error-handling assumptions break?

4. For your most critical operation, walk me through every failure scenario and how you'd recover.

5. Why validate the same data at both client and server? What failure would you miss if you didn't?
