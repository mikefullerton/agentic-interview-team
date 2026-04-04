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

## Manifest

- specialty-teams/data-persistence/idempotency.md
- specialty-teams/data-persistence/immutability.md
- specialty-teams/data-persistence/offline-and-connectivity.md
- specialty-teams/data-persistence/reliability-compliance.md

## Exploratory Prompts

1. What if every data operation had to be reversible? How would that change your design?

2. Why are mutable shared state and concurrency bugs so related? What would eliminating that category of bugs look like?

3. If you couldn't use transactions, how would you ensure consistency?

4. What's the relationship between data corruption and user trust? What's the worst data bug you could have?
