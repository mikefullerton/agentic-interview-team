---

id: AF78FFED-0E66-42BE-AB40-EF1BD6A49DD2
title: "Access Pattern Analysis"
domain: agentic-cookbook://guidelines/implementing/data/access-pattern-analysis
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Rules for analyzing query access patterns to drive schema and index decisions, covering read-heavy vs write-heavy tradeoffs, designing for WHERE/JOIN/ORDER BY, identifying missing indexes, and sync-specific batch sizing and transaction patterns."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - access-patterns
  - performance
  - schema-design
  - sync
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
  - guidelines/data/indexing.md
  - guidelines/data/transactions-and-concurrency.md
  - guidelines/data/query-optimization.md
references:
  - https://sqlite.org/queryplanner.html
  - https://www.sqlite.org/eqp.html
  - https://www.powersync.com/blog/sqlite-optimizations-for-ultra-high-performance
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - schema-design
  - performance-optimization
---

# Access Pattern Analysis

Schema and index decisions must follow from actual query patterns, not from assumptions about what might be queried. Before adding a column, index, or table, identify the queries that will use it and verify the design supports them efficiently.

## Start With the Queries, Not the Schema

MUST answer these questions before finalizing any schema:

1. What are the most frequent queries? What columns appear in WHERE, JOIN, and ORDER BY?
2. What are the most expensive queries? (Use `EXPLAIN QUERY PLAN` and `ANALYZE`.)
3. Is this table read-heavy or write-heavy? What is the read-to-write ratio?
4. Are reads latency-sensitive (user-facing) or throughput-sensitive (background batch)?
5. What is the expected row count — today and at 10x scale?

The answers drive every subsequent decision: index selection, composite key ordering, WAL vs rollback journal, batch size, and connection count.

## Design for WHERE, JOIN, and ORDER BY

A column belongs in an index if and only if queries will filter, join, or sort on it.

```sql
-- Before creating this index, confirm: which queries use status and created_date together?
CREATE INDEX idx_orders_status_date ON orders(status, created_date DESC);
```

MUST NOT add an index speculatively. An index that no query uses costs write performance with no read benefit.

SHOULD maintain a query inventory: a list of the significant queries for each table, their frequency, and which columns they filter on. Use this inventory to verify that every index earns its place, and that every frequent query has index support.

**Column order in composite indexes follows query patterns:**
- Equality filters (`=`, `IN`) go first
- Range filters (`<`, `>`, `BETWEEN`) go last
- ORDER BY columns go last when the query has no range filter, enabling index-ordered scans that eliminate sort steps

## Read-Heavy vs Write-Heavy Tradeoffs

**Read-heavy tables** (lookups, reporting, list views):
- Add covering indexes for the hottest queries — eliminate table lookups entirely
- Use `mmap_size` and a larger `cache_size` to keep working set in memory
- Prefer `SELECT` with specific columns over `SELECT *` to maximize covering index usage
- Run `ANALYZE` regularly to keep query planner statistics current

**Write-heavy tables** (event logs, outboxes, audit trails, sync change logs):
- Minimize the number of indexes — each index adds overhead to every INSERT, UPDATE, and DELETE
- A heavily indexed table can sustain 5x slower inserts compared to the same table with no secondary indexes
- Use partial indexes to limit index size to the rows that matter
- Batch writes in explicit transactions (100–1,000 rows per transaction for general use)
- Append-only tables (insert but never update) may need no secondary indexes at all beyond the primary key

**Mixed workload tables** (the common case):
- Profile the actual read/write ratio before adding indexes
- One index on the most selective filter column often covers 80% of the read benefit
- Add additional indexes only when profiling confirms they are needed

## Identifying Missing Indexes

The query planner signals missing index opportunities in `EXPLAIN QUERY PLAN` output:

```sql
EXPLAIN QUERY PLAN SELECT * FROM orders WHERE customer_id = 42;
```

Signals to act on:
- `SCAN orders` — full table scan; an index on `customer_id` would help
- `AUTOMATIC INDEX` — SQLite built a temporary index at query time; a permanent index would be faster
- `USE TEMP B-TREE FOR ORDER BY` — the sort is happening in memory; an index on the ORDER BY columns may eliminate it
- `CORRELATED SCALAR SUBQUERY` — runs per outer row; restructure as a JOIN

```sql
-- Enable automatic query plan output in the CLI during development
.eqp on
```

Also monitor `sqlite_stat1` after running `ANALYZE` to see actual row counts per index. If an index covers a column with very low cardinality on a large table, it may not help — the planner may prefer a full scan.

## Sync-Specific Access Patterns

Sync workloads have predictable query shapes. Design for them explicitly.

### Unsynced record queries

The most critical sync query: "what changed since the last sync?"

```sql
SELECT * FROM tasks
WHERE last_synced_at IS NULL
   OR updated_at > last_synced_at;
```

This query runs on every sync cycle. MUST have an index that covers it:

```sql
CREATE INDEX idx_tasks_sync_status ON tasks(last_synced_at, updated_at)
  WHERE last_synced_at IS NULL OR updated_at > last_synced_at;
```

Verify with `EXPLAIN QUERY PLAN` that this shows `SEARCH ... USING INDEX`, not `SCAN`.

### Outbox and change log queries

```sql
-- Outbox: pending entries to upload
SELECT * FROM outbox WHERE status = 'pending' ORDER BY next_attempt_at;

-- Change log: unsynced entries
SELECT * FROM change_log WHERE synced = 0 ORDER BY changed_at;
```

Both benefit from partial indexes on the filter condition:

```sql
CREATE INDEX idx_outbox_pending ON outbox(status, next_attempt_at)
  WHERE status = 'pending';

CREATE INDEX idx_changelog_unsynced ON change_log(synced, changed_at)
  WHERE synced = 0;
```

Partial indexes remain small even as the underlying table grows, because they only index the rows still in the active state.

### Soft-delete filter

Nearly every application query excludes deleted rows. Account for this in index design:

```sql
-- If most queries filter WHERE is_deleted = 0, include is_deleted in composite indexes
-- OR use a partial index on the active subset
CREATE INDEX idx_tasks_active_status ON tasks(status, created_date)
  WHERE is_deleted = 0;
```

## Batch Size for Sync Operations

Batch size is an access pattern decision: too small, and HTTP overhead dominates; too large, and a failed request wastes work.

| Context | Recommended Batch Size | Rationale |
|---------|----------------------|-----------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Mobile (unstable network) | 50–100 records | Smaller batches survive connection drops |
| Desktop (stable network) | 500–1,000 records | Reduces HTTP round-trips |
| Initial bootstrap | 1,000–5,000 records | Fast initial sync is critical for UX |
| Background sync | 100–500 records | Balances throughput with UI responsiveness |

MUST wrap each sync batch in a single transaction. Applying changes row-by-row in autocommit mode pays an fsync per row — at 30ms+ per fsync, a 500-record batch would take 15 seconds.

```sql
BEGIN IMMEDIATE;
-- apply all changes in the batch
COMMIT;
```

For bulk ingestion (initial sync or large imports), use JSON bulk operations to avoid SQLite's per-statement parameter limit and reduce round-trips:

```sql
-- Bulk insert via JSON: single statement for an entire batch
INSERT INTO tasks (id, title, status)
SELECT e->>'id', e->>'title', e->>'status'
FROM json_each(?) e;
```

## Transaction Management During Sync

MUST use `BEGIN IMMEDIATE` for sync write transactions (not `BEGIN DEFERRED`). `IMMEDIATE` acquires the write lock at transaction start, preventing mid-batch lock failures that would require rolling back the entire batch.

```python
def apply_sync_batch(changes, db):
    db.execute("BEGIN IMMEDIATE")
    try:
        for change in changes:
            apply_change(db, change)
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise
```

MUST NOT hold the write lock open while waiting for network responses. The pattern is: fetch the batch from the server, then open the transaction, apply all changes, commit. Network I/O happens outside the transaction boundary.

**Connection separation for sync:**
- One dedicated write connection for sync writes (prevents `SQLITE_BUSY` from competing writers)
- Separate read connections for UI queries that run during sync
- Set `busy_timeout = 5000` on all connections to absorb brief contention without returning errors

This connection strategy, combined with WAL mode, allows the sync writer to apply batches while the UI continues to read — the fundamental concurrency requirement for a responsive offline-first application.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
