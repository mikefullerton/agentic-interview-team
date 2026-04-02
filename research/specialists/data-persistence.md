# Data & Persistence Specialist

## Domain Coverage
Storage, sync, conflict resolution, migration, offline data, consistency models, concurrency, transactions, idempotency, immutability, schema design.

## Cookbook Sources
- `cookbook/principles/idempotency.md`
- `cookbook/principles/immutability-by-default.md`
- `cookbook/guidelines/networking/offline-and-connectivity.md`
- `cookbook/compliance/reliability.md`

## Structured Questions

1. Walk me through how data flows in your application. Where does it originate? How is it fetched, cached, and synchronized?

2. What's your consistency model? User changes on phone and another device — how do they sync? Both change the same data — what happens?

3. Describe your concurrency model. Can two threads/tasks mutate the same data? How do you prevent race conditions?

4. How do you handle partial failures? User action involves multiple steps (update local, sync to server, update cache) — step 2 fails, what happens?

5. What's your relationship with transactions? Do you use them? How far do they span?

6. Tell me about a data bug you've encountered. What caused it? How discovered? How fixed?

7. Offline scenarios — user makes changes while offline, how do they sync when back? Conflict resolution strategy?

8. What makes an operation "idempotent"? Are your critical operations idempotent? How do you ensure it?

9. How do you manage mutable state? All mutation in one place, or scattered? How do you reason about state changes?

10. Testing strategy for data/persistence — concurrent access? Partial failures?

11. Large database schema migration — what's the process? Backwards compatibility?

12. Database versioning strategy — how do you manage schema changes across app versions?

## Exploratory Prompts

1. What if every data operation had to be reversible? How would that change your design?

2. Why are mutable shared state and concurrency bugs so related? What would eliminating that category of bugs look like?

3. If you couldn't use transactions, how would you ensure consistency?

4. What's the relationship between data corruption and user trust? What's the worst data bug you could have?
