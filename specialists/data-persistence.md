# Data & Persistence Specialist

## Role
Storage, sync, conflict resolution, migration, offline data, consistency models, concurrency, transactions, idempotency, immutability, schema design.

## Persona
(coming)

## Cookbook Sources
- `principles/idempotency.md`
- `principles/immutability-by-default.md`
- `guidelines/networking/offline-and-connectivity.md`
- `compliance/reliability.md`

## Specialty Teams

### idempotency
- **Artifact**: `principles/idempotency.md`
- **Worker focus**: User actions and system operations safe to repeat without duplicate side effects; buttons debounced or disabled during async operations; idempotency keys on API calls with side effects; database migrations safe to run multiple times; state transitions check current state before applying
- **Verify**: Submit buttons disabled or debounced during in-flight requests; idempotency keys present on write API calls; migration scripts use IF NOT EXISTS or equivalent guards; state transition logic reads current state before writing

### immutability
- **Artifact**: `principles/immutability-by-default.md`
- **Worker focus**: Mutable shared state eliminated as the root cause of concurrency bugs; `let`/`val`/`const` used by default; value types (structs, data classes) preferred over reference types; mutation contained behind clear boundaries (actors, StateFlow, useState)
- **Verify**: No `var`/`var` declarations where `let`/`val` would suffice; mutable state confined to a single owner (actor, ViewModel, store); no shared mutable state across concurrent contexts; data classes or structs used for domain models

### offline-and-connectivity
- **Artifact**: `guidelines/networking/offline-and-connectivity.md`
- **Worker focus**: Local-first design with background sync; optimistic updates with rollback on server failure; queue-based outbox for mutations drained on reconnect; conflict detection via ETags/version numbers with 409 response; `last_synced_at` per entity for delta sync; clear connectivity status shown to user; user work never silently discarded
- **Verify**: Offline mutations queued and not silently dropped; optimistic UI rolled back on server error; connectivity status visible to user; `last_synced_at` tracked per synced entity; conflict scenarios return 409 with both versions; offline scenarios tested (airplane mode, flaky connections)

### reliability-compliance
- **Artifact**: `compliance/reliability.md`
- **Worker focus**: 8 compliance checks — error-recovery, graceful-degradation, fault-tolerance, state-recovery, idempotent-operations, timeout-handling, data-integrity, health-observability
- **Verify**: Each compliance check has a status (passed/failed/partial/n-a) with evidence; state restored correctly after process restart; write operations that may be retried are idempotent; data integrity validated on read and write with corrupt data detected and reported

## Exploratory Prompts

1. What if every data operation had to be reversible? How would that change your design?

2. Why are mutable shared state and concurrency bugs so related? What would eliminating that category of bugs look like?

3. If you couldn't use transactions, how would you ensure consistency?

4. What's the relationship between data corruption and user trust? What's the worst data bug you could have?
