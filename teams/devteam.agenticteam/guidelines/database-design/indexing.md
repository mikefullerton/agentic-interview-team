---

id: 02E9042D-0D15-47AC-9361-2F16980A03CA
title: "Indexing"
domain: agentic-cookbook://guidelines/implementing/data/indexing
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Rules for creating effective indexes in SQLite and PostgreSQL, covering B-tree fundamentals, composite ordering, covering indexes, partial and expression indexes, sync metadata indexes, and when not to index."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - indexing
  - performance
  - query-planning
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
  - guidelines/data/query-optimization.md
references:
  - https://sqlite.org/queryplanner.html
  - https://sqlite.org/partialindex.html
  - https://sqlite.org/expridx.html
  - https://www.sqlite.org/eqp.html
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - performance-optimization
  - schema-design
---

# Indexing

Indexes are the primary lever for query performance. Used correctly, they cut lookups from O(N) to O(log N). Used carelessly, they degrade write performance without helping reads.

## B-Tree Fundamentals

SQLite stores every table as a B+ tree keyed by rowid. Every index is a separate B+ tree keyed by the indexed columns with rowid appended. A query that uses an index performs two binary searches: one on the index tree to find the rowid, then one on the table tree to retrieve the row. A covering index eliminates the second lookup entirely.

## Composite Index Column Ordering

Column order in a multi-column index is not arbitrary. The query planner can only use a composite index from its left prefix — gaps break the chain.

**MUST follow:**
- Equality columns (`=`, `IN`, `IS`) go first.
- Inequality columns (`<`, `>`, `<=`, `>=`, `BETWEEN`) go last — only the rightmost used column can use a range constraint.
- Columns to the right of an inequality are not used for filtering.

```sql
-- Given: CREATE INDEX idx_a_b_c ON t(a, b, c);
WHERE a = 1 AND b = 2 AND c > 3   -- uses all 3 columns
WHERE a = 1 AND b > 2             -- uses a and b only
WHERE b = 2                        -- cannot use this index (no left prefix)
```

**MUST NOT** create an index that is a prefix of an existing index. If you have `(a, b, c)`, you do not need separate indexes on `(a)` or `(a, b)`. Redundant indexes waste write budget with no read benefit.

## Covering Indexes

A covering index includes every column the query reads, so SQLite never has to touch the table. This roughly halves the number of disk lookups.

```sql
-- Query needs fruit, state, and price
SELECT price FROM fruitsforsale WHERE fruit = 'Orange' AND state = 'CA';

-- Covering index: filter columns first, then the output column
CREATE INDEX idx_fruit_state_price ON fruitsforsale(fruit, state, price);
```

`EXPLAIN QUERY PLAN` confirms with `USING COVERING INDEX`. Aim for covering indexes on hot read paths where the query shape is stable.

## Partial Indexes

Index only the rows a query actually touches. A partial index is smaller, faster to write through, and can enforce conditional uniqueness.

```sql
-- Index only pending outbox rows (the ones that matter for queries)
CREATE INDEX idx_outbox_pending ON outbox(status, next_attempt_at)
  WHERE status = 'pending';

-- Conditional uniqueness: only one team leader per team
CREATE UNIQUE INDEX idx_team_leader ON person(team_id)
  WHERE is_team_leader;
```

**MUST:** The query WHERE clause must include the partial index WHERE clause terms (literally or by implication) for the planner to use the index. A partial index on `status = 'pending'` is not used by a query without `status = 'pending'` in its filter.

Partial indexes require SQLite 3.8.0+. Databases with partial indexes cannot be read by older SQLite versions.

## Expression Indexes

Index the result of a deterministic expression rather than a raw column.

```sql
CREATE INDEX idx_upper_last ON employees(UPPER(last_name));
CREATE INDEX idx_event_date ON events(date(created_at));
```

**MUST:** The expression in the query must match the index definition exactly — the planner does no algebra.

```sql
-- Given: CREATE INDEX idx_xy ON t(x + y);
WHERE x + y > 10   -- uses the index
WHERE y + x > 10   -- does NOT use the index (operand order differs)
```

**Restrictions:** Only deterministic functions, no subqueries, only columns from the indexed table. Expression indexes require SQLite 3.9.0+.

## JSON Indexing via Generated Columns

To query JSON fields at B-tree speed, extract them as virtual generated columns and index those columns.

```sql
ALTER TABLE events ADD COLUMN event_type TEXT
  GENERATED ALWAYS AS (json_extract(data, '$.type')) VIRTUAL;

CREATE INDEX idx_event_type ON events(event_type);

-- Now uses index:
SELECT * FROM events WHERE event_type = 'click';
```

Use VIRTUAL (not STORED) unless reads vastly outnumber writes. VIRTUAL columns are computed on read, carry no storage cost, and can be added with `ALTER TABLE`.

## Index Strategy for Sync Metadata Columns

Sync queries follow predictable patterns. Index for them explicitly.

```sql
-- Find unsynced records (the most important sync query)
CREATE INDEX idx_tasks_sync_status ON tasks(last_synced_at, updated_at)
  WHERE last_synced_at IS NULL OR updated_at > last_synced_at;

-- Change log: unsynced changes only
CREATE INDEX idx_changelog_unsynced ON change_log(synced, changed_at)
  WHERE synced = 0;

-- Soft-delete filter (nearly every query excludes deleted rows)
CREATE INDEX idx_tasks_active ON tasks(updated_at)
  WHERE is_deleted = 0;
```

Always verify with `EXPLAIN QUERY PLAN` that sync queries show `SEARCH ... USING INDEX`, not `SCAN`.

## EXPLAIN QUERY PLAN

MUST use `EXPLAIN QUERY PLAN` to validate index usage before deploying schema changes.

```sql
EXPLAIN QUERY PLAN SELECT * FROM orders WHERE customer_id = 42;
```

Key output terms:
- `SCAN table` — full table scan; check whether an index would help
- `SEARCH table USING INDEX` — index-assisted lookup
- `SEARCH table USING COVERING INDEX` — no table lookup needed (best)
- `USE TEMP B-TREE FOR ORDER BY` — a sort step is required; an index on the ORDER BY columns may eliminate it
- `AUTOMATIC INDEX` — SQLite created a temporary index; a permanent index would help
- `CORRELATED SCALAR SUBQUERY` — runs once per outer row; rewrite as a JOIN

Enable automatic query plan output in the SQLite CLI: `.eqp on`.

## When NOT to Index

Every index is maintained on every INSERT, UPDATE, and DELETE. The number of indexes on a table is the dominant factor for insert performance — heavily indexed tables can see 5x slower inserts.

**SHOULD NOT index:**
- Columns that are never in a WHERE, JOIN, or ORDER BY clause.
- Low-cardinality columns (e.g., a boolean `is_active` on a table where 99% of rows are active) — a full table scan is often faster.
- Tables that are write-only or insert-heavy with infrequent reads.

Run `PRAGMA optimize` periodically to keep query planner statistics current. Monitor with `SELECT * FROM sqlite_stat1;` (populated by `ANALYZE`) to see which indexes the planner is actually using.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
