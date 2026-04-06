# Database Specialist Design

## Summary

Redesign the `platform-database` specialist from 3 specialty teams to 22 specialty teams + 3 consulting teams, organized around schema design, performance, operations, and local-remote sync. This is the most complex specialist in the system because database decisions are deeply interdependent — a primary key choice cascades into sync, performance, schema evolution, and type mapping simultaneously.

## Use Cases

1. **Schema planning and analysis** — designing and improving database schemas for data access patterns, speed, search, resilience, and flexibility
2. **Sync architecture** — planning server databases (PostgreSQL), local databases (SQLite), and the synchronization strategy between them

## Design Principles

- **Single responsibility per team** — each specialty team answers one focused question with tightly curated research material
- **Cross-database by default** — teams understand both SQLite and PostgreSQL implications within their domain, not siloed by database engine
- **Consulting teams as required gates** — 3 consulting teams review every specialty team's output, catching cross-cutting concerns that no single team owns
- **Quality over speed** — the consulting layer adds steps but prevents costly retrofits from missed interdependencies

## Consulting Teams

Consulting teams are specialty teams that sit in a verification role in the pipeline. They follow the same worker/verifier structure as every other specialty team. Every specialty team's output passes through all consulting teams.

Each consulting team produces one of two response types:
- **VERIFIED** — "I reviewed this, here's my assessment" (with findings, approvals, or modifications)
- **NOT-APPLICABLE** — "Nothing in this output falls within my responsibilities" (with brief explanation)

Both responses go through the consulting team's verifier before becoming final.

**Note:** Consulting-team support is a new pipeline feature that must be implemented before this specialist can be fully deployed. This spec assumes that feature exists.

### Pipeline Flow

```
specialty-team: worker produces output → verifier checks
    → cross-database-compatibility: worker reviews → verifier checks → VERIFIED or NOT-APPLICABLE
    → sync-impact: worker reviews → verifier checks → VERIFIED or NOT-APPLICABLE
    → access-pattern-coherence: worker reviews → verifier checks → VERIFIED or NOT-APPLICABLE
    → final verified output
```

### 1. cross-database-compatibility

**Responsibility:** Ensures every schema decision works on both SQLite and PostgreSQL. Catches type incompatibilities, PK strategy conflicts, constraint gaps, and representation mismatches between local and server databases.

**Source material:**
- `docs/research/database/sync-sqlite.md` § 24 Type Mapping Between SQLite and Server Databases
- `docs/research/database/schema-design.md` § 2 Data Types and Type Affinity, § 3 Primary Key Strategies
- `docs/research/database/decision-frameworks.md` § 5 Local Database vs Server Database Design

**Example VERIFIED findings:**
- "The primary-keys team recommended BLOB UUIDv7 for SQLite. Confirmed: PostgreSQL 17+ supports `uuid_generate_v7()` natively. Type mapping is clean."
- "The constraints team added `CHECK (status IN ('active', 'inactive'))`. PostgreSQL equivalent confirmed. However, SQLite uses INTEGER for booleans while PostgreSQL uses BOOLEAN — ensure the sync layer handles conversion."

**Example NOT-APPLICABLE:**
- "The backup-and-recovery team's output covers SQLite backup API and VACUUM strategy. These are single-database operations with no cross-database implications."

### 2. sync-impact

**Responsibility:** Ensures non-sync teams account for synchronization implications. Catches decisions that would break sync, create merge conflicts, or make offline operation difficult.

**Source material:**
- `docs/research/database/sync-strategies.md` (full document)
- `docs/research/database/decision-frameworks.md` § 1 Choosing a Sync Strategy, § 2 Choosing a Sync Tool

**Example VERIFIED findings:**
- "The normalization team recommended denormalizing user display names onto the tasks table. Sync impact: denormalized data must be kept in sync across devices. If a user changes their display name, every task row must be updated and synced. Consider whether this denormalization is worth the sync cost."
- "The schema-evolution team proposed dropping a column. Sync impact: connected clients with older schema versions will send data for this column. The server must silently ignore unknown fields during sync, or clients must be force-upgraded first."

**Example NOT-APPLICABLE:**
- "The naming-conventions team's output covers column naming patterns. Naming does not affect sync behavior."

### 3. access-pattern-coherence

**Responsibility:** Ensures structural decisions serve actual query patterns. Catches schemas that look correct but perform poorly under real-world access patterns.

**Source material:**
- `docs/research/database/performance-and-tuning.md` § 7 Indexes, § 11 Query Optimization
- `docs/research/database/decision-frameworks.md` § 6 Schema Design Pattern Selection

**Example VERIFIED findings:**
- "The relationships team designed a many-to-many join table for task-tags. The hot-path query filters tasks by tag — confirmed the join table has an index on `(tag, task_id)` for this access pattern."
- "The json-columns team stored metadata as JSON. Access pattern analysis: the app filters by `metadata->>'category'` on every list view. A generated column with index is needed — raw JSON extraction on every query will cause full table scans."

**Example NOT-APPLICABLE:**
- "The clock-systems team's output covers choosing between HLC and monotonic versioning. This is a sync protocol decision, not a query pattern decision."

## Specialty Teams

### Schema Design (9 teams)

#### 1. naming-conventions
**Responsibility:** snake_case for all identifiers, table naming (plural vs singular), PK/FK column naming (`table_name_id` not bare `id`), reserved word avoidance, index/constraint/trigger naming patterns.

**Source:** `docs/research/database/schema-design.md` § 1

#### 2. data-types
**Responsibility:** SQLite type affinity and the 5-rule algorithm, STRICT tables, the STRING gotcha, NUMERIC affinity behavior, comparison pitfalls, type mapping between SQLite and PostgreSQL (boolean, date, UUID, JSON, enum representation on each side).

**Source:** `docs/research/database/schema-design.md` § 2 + `docs/research/database/sync-sqlite.md` § 24

#### 3. primary-keys
**Responsibility:** INTEGER PRIMARY KEY (rowid alias), AUTOINCREMENT tradeoffs, UUID (TEXT vs BLOB, v4 vs v7), WITHOUT ROWID tables, hybrid approaches (integer PK + UUID for API), cross-database PK compatibility for synced tables.

**Source:** `docs/research/database/schema-design.md` § 3 + `docs/research/database/sync-sqlite.md` § 20.1

#### 4. foreign-keys
**Responsibility:** PRAGMA foreign_keys = ON (the critical first step), FK declaration (inline vs table-level), ON DELETE/UPDATE actions (CASCADE, SET NULL, RESTRICT), deferred constraints, NULL bypass behavior, FK column indexing, composite FKs, ALTER TABLE restrictions.

**Source:** `docs/research/database/schema-design.md` § 4

#### 5. constraints-and-validation
**Responsibility:** CHECK constraint syntax and evaluation, enum-like constraints, boolean enforcement, range/pattern validation, multi-column constraints, NULL truthiness in CHECK, conflict resolution, disabling checks for migration.

**Source:** `docs/research/database/schema-design.md` § 5

#### 6. relationships
**Responsibility:** One-to-many (FK on child), many-to-many (join tables), polymorphic FKs (discriminator column vs supertype/base table vs nullable-per-type), self-referential relationships, tree hierarchies (adjacency list, closure table, nested sets — with decision table for selection).

**Source:** `docs/research/database/schema-design.md` § 6 (Polymorphic Foreign Keys, Adjacency Lists and Tree Hierarchies)

#### 7. normalization-and-denormalization
**Responsibility:** 3NF as starting point, selective denormalization of measured hotspots, SQLite-specific tradeoff (embedded = zero network latency, so less pressure to denormalize), benchmark-informed decisions, denormalization and its interaction with sync.

**Source:** `docs/research/database/schema-design.md` § 6 (Normalized vs Denormalized)

#### 8. json-columns
**Responsibility:** JSON storage in TEXT columns, extraction operators (`json_extract`, `->>`, `->`), `json_each` for arrays, modification functions (`json_set`, `json_insert`, `json_replace`, `json_remove`), aggregation (`json_group_array`, `json_group_object`), validation, generated columns for B-tree indexing of JSON fields, JSONB on PostgreSQL, when JSON is a schema smell vs a legitimate tool.

**Source:** `docs/research/database/schema-design.md` § 6 (JSON Columns, Generated Columns for JSON Indexing)

#### 9. schema-evolution
**Responsibility:** Migration strategies (user_version pragma, migration tracking table), ALTER TABLE limitations in SQLite, backwards-compatible changes, sync-compatible migrations (add-only columns, defaults required, idempotent, wrapped in transactions), testing migrations against every previous version.

**Source:** `docs/research/database/operations-and-maintenance.md` § 13 + `docs/research/database/sync-strategies.md` § 3.4

### Performance (4 teams)

#### 10. indexing
**Responsibility:** B-tree index fundamentals, partial indexes (SQLite 3.8.0+), expression indexes, composite index column ordering, covering indexes, EXPLAIN QUERY PLAN interpretation, when NOT to index (small tables, low-selectivity columns, write-heavy tables), sync metadata indexes (isDirty, sync_version, unsynced changes).

**Source:** `docs/research/database/performance-and-tuning.md` § 7 + `docs/research/database/sync-sqlite.md` § 27.3

#### 11. query-optimization
**Responsibility:** SQLite query planner behavior, rewriting slow queries, avoiding full table scans, JSON query performance, correlated subquery elimination, CTEs vs subqueries, UNION ALL vs UNION.

**Source:** `docs/research/database/performance-and-tuning.md` § 11

#### 12. transactions-and-concurrency
**Responsibility:** WAL mode (why, how, checkpoint management), journal modes comparison, BEGIN IMMEDIATE vs DEFERRED (why IMMEDIATE for sync), connection strategies (single writer + multiple readers), busy_timeout, PRAGMA tuning for production (synchronous, cache_size, journal_size_limit, foreign_keys), WAL benefits for concurrent sync reads/writes.

**Source:** `docs/research/database/performance-and-tuning.md` § 9, 10, 12 + `docs/research/database/sync-sqlite.md` § 27.4

#### 13. access-pattern-analysis
**Responsibility:** Analyzing what queries will hit a schema, read-heavy vs write-heavy design tradeoffs, designing for WHERE/JOIN/ORDER BY, identifying missing indexes from query patterns, batch size recommendations for sync, transaction management during sync operations.

**Source:** `docs/research/database/performance-and-tuning.md` § 11 + `docs/research/database/sync-sqlite.md` § 27.1, 27.2

### Operations (2 teams)

#### 14. backup-and-recovery
**Responsibility:** SQLite backup API (online backup), Litestream for streaming WAL replication, corruption detection (`PRAGMA integrity_check`), recovery from corrupt databases, VACUUM strategy (when, how, incremental vs full), database size monitoring and management, tombstone purging.

**Source:** `docs/research/database/operations-and-maintenance.md` § 14 + `docs/research/database/sync-sqlite.md` § 27.5

#### 15. testing
**Responsibility:** Testing with SQLite (in-memory databases for speed, file-based for fidelity), test fixtures and seed data, migration testing (forward and backward), testing sync logic, testing conflict resolution.

**Source:** `docs/research/database/operations-and-maintenance.md` § 18

### Sync (7 teams)

#### 16. sync-schema-design
**Responsibility:** Dual schema design (local SQLite + server PostgreSQL), UUID primary keys for offline creation, soft deletes and tombstone patterns (flag column vs tombstone table), dirty tracking strategies (isDirty flag vs change log table vs edit operations), version columns for optimistic concurrency, timestamp columns (created_at, updated_at, last_synced_at), sync metadata tables.

**Source:** `docs/research/database/sync-sqlite.md` § 20 + `docs/research/database/sync-strategies.md` § 5.4

#### 17. conflict-resolution
**Responsibility:** Last-Write-Wins (LWW) implementation, server-wins vs client-wins policies, field-level merge (three-way comparison with base version), CRDTs (LWW-Register, G-Counter, PN-Counter, OR-Set, RGA), Operational Transformation, conflict queues for manual resolution, choosing strategy per data type and domain tolerance.

**Source:** `docs/research/database/sync-strategies.md` § 1

#### 18. sync-protocol
**Responsibility:** Push/pull/bidirectional sync, combined push/pull in single round trip, full sync vs incremental/delta sync, change tracking approaches (flag columns, change log, Session Extension), batch sync with pagination, idempotent operations (UPSERT patterns, idempotency keys), outbox pattern (transactional dual-write), retry with exponential backoff.

**Source:** `docs/research/database/sync-strategies.md` § 2

#### 19. clock-systems
**Responsibility:** Physical clocks (simple, clock-skew vulnerable), Lamport timestamps (causal ordering, no concurrency detection), vector clocks (concurrency detection, O(n) space), Hybrid Logical Clocks (best of both, 64-bit, recommended), server-assigned monotonic versions (simplest for client-server), choosing the right clock for the architecture.

**Source:** `docs/research/database/sync-strategies.md` § 4

#### 20. offline-first-architecture
**Responsibility:** WAL mode as foundation for offline, operation queue pattern, optimistic UI updates (write local + enqueue, read local, sync background), rollback on server rejection, schema migrations while device is offline, data expiry and cache invalidation, VACUUM after pruning, connectivity-aware sync scheduling.

**Source:** `docs/research/database/sync-strategies.md` § 3

#### 21. sync-engine-design
**Responsibility:** Sync orchestrator architecture (layers: app → orchestrator → content type handlers → transport → local DB), entity-agnostic Syncable interface, the sync cycle (collect → package → send → receive → apply → checkpoint), sync scheduling (periodic, event-driven, background daemon with platform-specific IPC), snapshot rebuilding after sync, error handling (exponential backoff, retry categories, circuit breakers).

**Source:** `docs/research/database/sync-strategies.md` § 5

#### 22. sync-tooling
**Responsibility:** Evaluating and selecting sync tools — SQLite Session Extension (built-in, binary changesets), cr-sqlite (CRDT-based merge), Litestream (WAL streaming backup), ElectricSQL (Postgres↔SQLite via logical replication), PowerSync (server-authoritative write path), Turso/libSQL (embedded replicas), sqlite-sync (CRDT extension). Tool comparison matrix, selection criteria.

**Source:** `docs/research/database/sync-sqlite.md` § 25

## Research Material

All source material lives in `docs/research/database/`:

| Document | Teams Served |
|----------|-------------|
| `schema-design.md` | 1-8 |
| `performance-and-tuning.md` | 10-13 |
| `operations-and-maintenance.md` | 9, 14, 15 |
| `sync-strategies.md` | 9, 16-21 |
| `sync-sqlite.md` | 2, 3, 10, 12-14, 16, 22 |
| `sync-case-studies.md` | Reference for all sync teams (Notion, Linear, Figma, Temporal patterns) |
| `decision-frameworks.md` | All consulting teams + teams making selection decisions |

## Exploratory Prompts

1. If your data model had to support a feature you haven't thought of yet, where would the pain be? What's inflexible?
2. What if you needed to change your primary database technology? What's tightly coupled?
3. If you had to guarantee zero data loss across regions during a network partition, what would you trade off?
4. What's the relationship between your data model and your domain model? Are they the same thing?
5. Walk me through what happens when two devices edit the same record offline. Where does each device's change end up?
6. What's the longest a device could be offline and still sync cleanly? What breaks first?

## Dependencies

- **Consulting-team pipeline feature** must be implemented before this specialist can be deployed with its consulting teams
- **Research documents** in `docs/research/database/` are already in place
- **Specialist persona** is still TBD (marked "coming" in current file)

## Implementation Order

1. Write this design spec (this document)
2. Design and implement consulting-team pipeline feature
3. Test consulting-team feature
4. Implement the 22 specialty team files
5. Implement the 3 consulting team files
6. Update the specialist definition (`specialists/platform-database.md`)
7. Test the full specialist with a real schema review
