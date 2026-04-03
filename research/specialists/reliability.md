# Reliability & Error Handling Specialist

## Role
Fail fast, idempotency, error categorization, retry strategies, timeout handling, graceful degradation, state recovery, data integrity, circuit breakers, monitoring.

## Persona
(coming)

## Cookbook Sources
- `principles/fail-fast.md`
- `principles/idempotency.md`
- `compliance/reliability.md`

## Specialty Teams

### fail-fast
- **Artifact**: `principles/fail-fast.md`
- **Worker focus**: Invalid state detected and surfaced immediately at the point of origin; assertions and preconditions in debug builds; input validation at system boundaries; typed errors returned rather than swallowed; no empty catch blocks; fail gracefully with clear messages in production, loudly in debug
- **Verify**: No empty catch blocks; typed error returns at system boundaries; debug builds use assertions/preconditions; no silent swallowing of exceptions; production error paths produce user-visible messages

### idempotency
- **Artifact**: `principles/idempotency.md`
- **Worker focus**: User actions and system operations safe to repeat without duplicate side effects; buttons debounced or disabled during async operations; idempotency keys on API calls with side effects; database migrations safe to run multiple times; state transitions check current state before applying
- **Verify**: Submit buttons disabled or debounced during in-flight requests; idempotency keys present on write API calls; migration scripts use IF NOT EXISTS or equivalent guards; state transition logic reads current state before writing

### reliability-compliance
- **Artifact**: `compliance/reliability.md`
- **Worker focus**: 8 compliance checks — error-recovery, graceful-degradation, fault-tolerance, state-recovery, idempotent-operations, timeout-handling, data-integrity, health-observability
- **Verify**: Each compliance check has a status (passed/failed/partial/n-a) with evidence; transient errors retried without user intervention; external dependency failure degrades gracefully (no crash); timed-out operations leave system in consistent state; persistent components emit health metrics

## Exploratory Prompts

1. What's the worst thing that could happen silently — a lost transaction, inconsistent state, data that never syncs? How would you catch it?

2. If one component fails, could it cascade? Database gets slow — how does that ripple through?

3. As you grow to 10x users, 100x traffic, which error-handling assumptions break?

4. For your most critical operation, walk me through every failure scenario and how you'd recover.

5. Why validate the same data at both client and server? What failure would you miss if you didn't?
