---
title: "Performance and Tuning"
domain: database
type: guideline
status: draft
created: 2026-04-03
modified: 2026-04-06
author: Mike Fullerton
summary: "Indexes, triggers, WAL mode, transaction management, query optimization, and PRAGMA settings for SQLite"
platforms:
  - sqlite
tags:
  - database
  - sqlite
  - performance
references:
  - https://sqlite.org/queryplanner.html
  - https://sqlite.org/wal.html
  - https://sqlite.org/lang_createtrigger.html
  - https://sqlite.org/pragma.html
related:
  - schema-design.md
  - operations-and-maintenance.md
---

# Performance and Tuning

> Indexes, triggers, WAL mode, transaction management, query optimization, and PRAGMA settings for SQLite.

---

## 7. Indexes

### B-Tree Architecture

SQLite stores all data in B-trees (specifically B+ trees). Each table is a B-tree keyed by rowid; each index is a separate B-tree keyed by the indexed columns with rowid appended. A lookup in a B-tree is O(log N), versus O(N) for a full table scan.

When a query uses an index, SQLite performs two binary searches: one on the index B-tree to find the rowid, then one on the table B-tree to retrieve the row. This is why covering indexes matter -- they eliminate the second lookup.

### Single-Column Indexes

```sql
CREATE INDEX idx_fruit ON fruitsforsale(fruit);
```

Reduces lookup from O(N) to O(log N). Still requires two binary searches (index + table).

### Multi-Column Indexes

```sql
CREATE INDEX idx_fruit_state ON fruitsforsale(fruit, state);
```

Rows are ordered by first column, with subsequent columns as tie-breakers. The query planner can use a multi-column index for any left-prefix of the indexed columns.

**Column ordering rules:**
- Equality columns (`=`, `IN`, `IS`) go first
- The rightmost used column can use inequalities (`<`, `>`, `<=`, `>=`, `BETWEEN`)
- No gaps allowed -- if columns are (a, b, c), you cannot use a and c without b
- Columns to the right of an inequality constraint are not used for indexing

```sql
-- Given index on (a, b, c):
WHERE a = 1 AND b = 2 AND c > 3   -- uses all 3 columns
WHERE a = 1 AND b > 2             -- uses a and b
WHERE a = 1                        -- uses only a
WHERE b = 2                        -- CANNOT use this index (no left-prefix)
```

**Rule of thumb:** "Your database schema should never contain two indices where one index is a prefix of the other." If you have an index on (a, b, c), you do not need a separate index on (a) or (a, b).

Source: [SQLite Query Planning](https://sqlite.org/queryplanner.html)

### Covering Indexes

A covering index includes all columns needed by a query, eliminating the table lookup entirely. This cuts the number of binary searches in half, roughly doubling query speed.

```sql
-- Query needs fruit, state, and price
SELECT price FROM fruitsforsale WHERE fruit = 'Orange' AND state = 'CA';

-- Covering index: includes the output column (price)
CREATE INDEX idx_fruit_state_price ON fruitsforsale(fruit, state, price);
```

EXPLAIN QUERY PLAN shows `USING COVERING INDEX` when this optimization applies:

```
QUERY PLAN
`--SEARCH fruitsforsale USING COVERING INDEX idx_fruit_state_price (fruit=? AND state=?)
```

Source: [SQLite Query Planning](https://sqlite.org/queryplanner.html)

### Partial Indexes

Index only a subset of rows by adding a WHERE clause. Reduces index size, speeds up writes, and can enforce conditional uniqueness.

```sql
-- Only index non-NULL values (useful when most rows are NULL)
CREATE INDEX idx_parent_po ON purchaseorder(parent_po)
  WHERE parent_po IS NOT NULL;

-- Enforce "only one team leader per team"
CREATE UNIQUE INDEX idx_team_leader ON person(team_id)
  WHERE is_team_leader;
```

**Query planner usage rules:**
- The partial index WHERE clause terms must appear (exactly or by implication) in the query WHERE clause
- `IS NOT NULL` in the index is satisfied by any comparison operator (`=`, `<`, `>`, `<>`, `IN`, `LIKE`, `GLOB`) on that column
- Expression matching is literal -- `b=6` matches `6=b` but NOT `b=3+3`

```sql
CREATE INDEX idx_active ON orders(customer_id) WHERE status = 'active';

-- Uses the partial index:
SELECT * FROM orders WHERE customer_id = 42 AND status = 'active';

-- Does NOT use the partial index (status term missing):
SELECT * FROM orders WHERE customer_id = 42;
```

Available since SQLite 3.8.0. Databases with partial indexes are unreadable by older versions.

Source: [SQLite Partial Indexes](https://www.sqlite.org/partialindex.html)

### Expression Indexes

Index the result of an expression rather than a raw column value.

```sql
CREATE INDEX idx_upper_last ON employees(UPPER(last_name));
CREATE INDEX idx_abs_amount ON account_change(acct_no, abs(amt));
CREATE INDEX idx_length_company ON customers(LENGTH(company));
```

**Critical constraint: exact expression matching.** The query planner does not do algebra. The expression in the query must match the index definition exactly:

```sql
-- Given: CREATE INDEX idx_xy ON t(x + y);
WHERE x + y > 10   -- USES the index
WHERE y + x > 10   -- does NOT use the index (different operand order)
```

**Restrictions:**
- Only deterministic functions allowed (no `random()`, `sqlite_version()`)
- Can only reference columns from the indexed table
- No subqueries
- Only usable in CREATE INDEX (not UNIQUE or PRIMARY KEY constraints)

Available since SQLite 3.9.0.

Source: [SQLite Indexes on Expressions](https://sqlite.org/expridx.html)

### Generated Columns + JSON Indexing

Generated columns (3.31.0+) let you extract values from JSON and index them at B-tree speed:

```sql
CREATE TABLE events (
  id INTEGER PRIMARY KEY,
  data TEXT  -- JSON blob
);

-- Virtual generated columns (computed on read, no storage cost)
ALTER TABLE events ADD COLUMN event_type TEXT
  GENERATED ALWAYS AS (json_extract(data, '$.type')) VIRTUAL;

ALTER TABLE events ADD COLUMN event_date TEXT
  GENERATED ALWAYS AS (json_extract(data, '$.date')) VIRTUAL;

-- Index the generated columns
CREATE INDEX idx_event_type ON events(event_type);
CREATE INDEX idx_event_date ON events(event_date);

-- Now this query uses B-tree index speed:
SELECT * FROM events WHERE event_type = 'click';
```

**VIRTUAL vs STORED:**
- VIRTUAL: computed on read, no disk space, can be added with ALTER TABLE
- STORED: computed on write, uses disk space, cannot be added with ALTER TABLE
- Use STORED when reads vastly outnumber writes; VIRTUAL otherwise

Source: [SQLite Generated Columns](https://sqlite.org/gencol.html)

### EXPLAIN QUERY PLAN

The essential tool for understanding index usage.

```sql
EXPLAIN QUERY PLAN SELECT * FROM orders WHERE customer_id = 42;
```

**Key output terms:**
- `SCAN table` -- full table scan (bad for large tables)
- `SEARCH table USING INDEX idx (col=?)` -- index lookup (good)
- `SEARCH table USING COVERING INDEX idx (col=?)` -- no table lookup needed (best)
- `USE TEMP B-TREE FOR ORDER BY` -- sorting required (index could eliminate this)
- `CORRELATED SCALAR SUBQUERY` -- runs once per outer row (expensive)
- `MULTI-INDEX OR` -- separate index lookups combined for OR conditions
- `AUTOMATIC INDEX` -- SQLite created a temporary index (permanent index would help)

```sql
-- Enabling automatic EXPLAIN QUERY PLAN in the CLI:
.eqp on
-- Now every query automatically shows its plan before results
```

Source: [SQLite EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)

### Over-Indexing Pitfalls

Every index must be maintained on every INSERT, UPDATE, and DELETE. The number of indexes on a table is the dominant factor for insert performance.

**Guidance:**
- Before creating an index, ask: "Will queries WHERE, JOIN, or ORDER BY this column?"
- Remove indexes that EXPLAIN QUERY PLAN never references
- Never have two indexes where one is a prefix of the other
- Run `PRAGMA optimize` periodically so the query planner has current statistics
- Monitor with: `SELECT * FROM sqlite_stat1;` (populated by ANALYZE)

**Benchmark reference:** With secondary indexes present, insert performance may reduce by up to 5x compared to a table with no secondary indexes.

Sources: [Use The Index, Luke - Insert](https://use-the-index-luke.com/sql/dml/insert), [Common Indexing Mistakes](https://www.slingacademy.com/article/common-mistakes-in-indexing-and-how-to-avoid-them-in-sqlite/)

---

## 8. Triggers

### Syntax

```sql
CREATE [TEMP | TEMPORARY] TRIGGER [IF NOT EXISTS] trigger_name
    {BEFORE | AFTER | INSTEAD OF} {DELETE | INSERT | UPDATE [OF column_name, ...]}
    ON table_name
    [FOR EACH ROW]
    [WHEN expression]
BEGIN
    -- one or more statements
END;
```

### Trigger Types

| Type | Works On | When It Fires |
|---|---|---|
| `BEFORE` | Tables only | Before the row modification |
| `AFTER` | Tables only | After the row modification |
| `INSTEAD OF` | Views only | Replaces the triggering operation entirely |

SQLite supports only `FOR EACH ROW` triggers (not `FOR EACH STATEMENT` like PostgreSQL).

### NEW and OLD References

| Event | `NEW.column` | `OLD.column` |
|---|---|---|
| INSERT | Available | Not available |
| UPDATE | Available (new values) | Available (old values) |
| DELETE | Not available | Available |

### Common Use Cases

#### 1. Audit Trail

```sql
CREATE TABLE audit_log (
    audit_log_id INTEGER PRIMARY KEY,
    table_name   TEXT NOT NULL,
    record_id    INTEGER NOT NULL,
    operation    TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values   TEXT,  -- JSON of old row
    new_values   TEXT,  -- JSON of new row
    change_date  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- After INSERT: log the new row
CREATE TRIGGER tr_documents_after_insert_audit
AFTER INSERT ON documents
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, operation, new_values)
    VALUES (
        'documents',
        NEW.document_id,
        'INSERT',
        json_object('title', NEW.title, 'body', NEW.body)
    );
END;

-- After UPDATE: log old and new values
CREATE TRIGGER tr_documents_after_update_audit
AFTER UPDATE ON documents
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values)
    VALUES (
        'documents',
        NEW.document_id,
        'UPDATE',
        json_object('title', OLD.title, 'body', OLD.body),
        json_object('title', NEW.title, 'body', NEW.body)
    );
END;

-- Before DELETE: log the deleted row
CREATE TRIGGER tr_documents_before_delete_audit
BEFORE DELETE ON documents
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, operation, old_values)
    VALUES (
        'documents',
        OLD.document_id,
        'DELETE',
        json_object('title', OLD.title, 'body', OLD.body)
    );
END;
```

#### 2. Automatic Timestamp Updates

```sql
CREATE TRIGGER tr_documents_after_update_timestamp
AFTER UPDATE ON documents
FOR EACH ROW
WHEN NEW.modification_date = OLD.modification_date OR NEW.modification_date IS NULL
BEGIN
    UPDATE documents
    SET modification_date = datetime('now')
    WHERE document_id = NEW.document_id;
END;
```

The WHEN clause prevents infinite recursion -- the trigger only fires when the timestamp was not explicitly set by the UPDATE statement.

#### 3. Business Rule Validation

```sql
CREATE TRIGGER tr_sales_before_insert_validate
BEFORE INSERT ON sales
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.sale_price < NEW.purchase_price THEN
            RAISE(ABORT, 'Sale price must not be less than purchase price')
    END;
END;
```

The `RAISE()` function is trigger-specific and provides error handling:
- `RAISE(ROLLBACK, 'message')` -- rolls back the entire transaction
- `RAISE(ABORT, 'message')` -- aborts the current statement, undoes its changes, but preserves prior statements in the transaction
- `RAISE(FAIL, 'message')` -- fails the current statement but keeps changes already made by it
- `RAISE(IGNORE)` -- silently skips the rest of the trigger and the triggering statement

#### 4. Maintaining Denormalized Data

```sql
-- Keep a cached count in the parent table
CREATE TRIGGER tr_line_items_after_insert_count
AFTER INSERT ON line_items
FOR EACH ROW
BEGIN
    UPDATE orders
    SET item_count = (SELECT count(*) FROM line_items WHERE order_id = NEW.order_id)
    WHERE order_id = NEW.order_id;
END;

CREATE TRIGGER tr_line_items_after_delete_count
AFTER DELETE ON line_items
FOR EACH ROW
BEGIN
    UPDATE orders
    SET item_count = (SELECT count(*) FROM line_items WHERE order_id = OLD.order_id)
    WHERE order_id = OLD.order_id;
END;
```

#### 5. INSTEAD OF Triggers on Views

```sql
CREATE VIEW active_customers AS
    SELECT customer_id, customer_name, email
    FROM customers
    WHERE is_active = 1;

CREATE TRIGGER tr_active_customers_instead_of_update
INSTEAD OF UPDATE ON active_customers
FOR EACH ROW
BEGIN
    UPDATE customers
    SET customer_name = NEW.customer_name,
        email = NEW.email
    WHERE customer_id = NEW.customer_id;
END;

-- Now you can UPDATE the view directly:
UPDATE active_customers SET email = 'new@example.com' WHERE customer_id = 42;
```

### Performance Implications

**Overhead sources:**
- SQLite opens a **statement journal** for any statement that fires triggers, adding file I/O even for simple operations.
- Each trigger body is a separate program that gets compiled and executed per affected row.
- Triggers that perform additional writes (INSERT into audit table, UPDATE a counter) multiply the I/O.
- Using `PRAGMA temp_store = MEMORY` reduces statement journal overhead by keeping it in memory.

**Practical advice:**
- Prefer `AFTER` triggers over `BEFORE` triggers. BEFORE triggers have undefined behavior if they modify or delete the row being processed.
- Keep trigger logic simple -- complex business logic belongs in application code where it can be versioned, tested, and debugged.
- Triggers are invisible at the SQL level. Document them heavily. Developers debugging slow INSERTs may not realize triggers are firing.
- Audit triggers on high-write tables can become a bottleneck. Consider batched/async logging for high-throughput scenarios.
- Test empirically -- one trigger on a moderate-volume table is usually fine; dozens of triggers on hot tables compound overhead.

### Restrictions Within Trigger Bodies

1. Table names must be unqualified (no `schema.table` syntax)
2. Non-TEMP triggers can only reference tables in the same database
3. TEMP triggers can access any attached database
4. No `INSERT INTO table DEFAULT VALUES`
5. No `INDEXED BY` / `NOT INDEXED` clauses
6. No `ORDER BY` / `LIMIT` clauses
7. No CTEs directly (but CTEs work inside subselects)

### Sources

- [CREATE TRIGGER](https://www.sqlite.org/lang_createtrigger.html) -- official trigger docs, syntax, restrictions
- [Creating Audit Tables with SQLite Triggers (Medium)](https://medium.com/@dgramaciotti/creating-audit-tables-with-sqlite-and-sql-triggers-751f8e13cf73)
- [SQLite Triggers (sql-easy.com)](https://www.sql-easy.com/learn/sqlite-trigger/)
- [Measuring and Reducing CPU Usage in SQLite](https://sqlite.org/cpu.html) -- performance measurement
- [SQLite Optimizations for Ultra High Performance (PowerSync)](https://www.powersync.com/blog/sqlite-optimizations-for-ultra-high-performance)

---

## 9. WAL Mode and Journal Modes

### Journal Mode Comparison

| Mode | Mechanism | Concurrent Reads | Write Speed | Durability |
|------|-----------|-----------------|-------------|------------|
| DELETE (default) | Rollback journal, deleted after txn | Blocked during writes | Slow (2x write) | Full |
| TRUNCATE | Rollback journal, truncated (not deleted) | Blocked during writes | Slightly faster than DELETE | Full |
| PERSIST | Rollback journal header zeroed | Blocked during writes | Slightly faster than DELETE | Full |
| WAL | Write-ahead log | Yes, concurrent with writes | Fast (1x write, sequential) | Full with synchronous=FULL |
| MEMORY | Journal in RAM only | Blocked during writes | Fast | None (crash = corruption) |
| OFF | No journal | Blocked during writes | Fastest | None (crash = corruption) |

### WAL Mode Details

```sql
PRAGMA journal_mode = WAL;
```

**How it works:** Changes are appended to a separate WAL file instead of modifying the database directly. The original database file stays intact. A COMMIT is just appending a commit record to the WAL -- no fsync of the database file required.

**Concurrency model:**
- Unlimited simultaneous readers
- One writer at a time
- Readers do not block writers; writers do not block readers
- Each reader sees a consistent snapshot from when its transaction started

**Performance advantages:**
- Writes are sequential (append-only to WAL), not random I/O
- Fewer fsync() calls than rollback journal
- Per-transaction overhead drops from 30ms+ to <1ms (with synchronous=NORMAL)

**Limitations:**
- All processes must be on the same machine (shared memory requirement)
- Cannot change page_size after entering WAL mode
- Very large transactions (multi-GB) may perform worse than rollback mode
- Creates additional -wal and -shm files alongside the database

### Checkpointing

Checkpointing transfers WAL content back to the main database file. Types:

```sql
PRAGMA wal_checkpoint(PASSIVE);   -- Non-blocking, does what it can
PRAGMA wal_checkpoint(FULL);      -- Blocks new writers until complete
PRAGMA wal_checkpoint(RESTART);   -- Blocks writers, resets WAL to beginning
PRAGMA wal_checkpoint(TRUNCATE);  -- Blocks writers, truncates WAL to zero bytes
```

**Automatic checkpointing:** By default, SQLite checkpoints when the WAL reaches 1000 pages.

```sql
-- Increase threshold for better write throughput (at cost of slower reads):
PRAGMA wal_autocheckpoint = 2000;

-- Disable automatic checkpointing (manual control only):
PRAGMA wal_autocheckpoint = 0;
```

**WAL growth prevention:** Three causes of unbounded WAL growth:
1. Automatic checkpointing disabled without manual replacement
2. Checkpoint starvation -- long-running readers prevent checkpoint from completing
3. Very large write transactions that block checkpointing

```sql
-- Limit WAL file size on disk (bytes, reclaimed after checkpoint):
PRAGMA journal_size_limit = 6144000;  -- 6MB
```

### When to Use Each Mode

- **WAL:** Default choice for most applications. Use when you have concurrent readers, need good write performance, and all access is from the same machine.
- **DELETE:** Use for maximum compatibility, network file systems, or when WAL limitations apply.
- **TRUNCATE:** Marginal speed improvement over DELETE on some filesystems.
- **OFF/MEMORY:** Only for ephemeral/rebuildable data where crash safety does not matter.

Sources: [SQLite WAL Documentation](https://sqlite.org/wal.html), [Fly.io SQLite WAL Internals](https://fly.io/blog/sqlite-internals-wal/), [SQLite Performance Tuning (phiresky)](https://phiresky.github.io/blog/2020/sqlite-performance-tuning/)

---

## 10. Transaction Management

### Implicit vs Explicit Transactions

Every SQL statement in SQLite runs inside a transaction. Without an explicit BEGIN, each statement gets its own implicit transaction with automatic COMMIT. This means individual INSERT statements each pay the full fsync cost.

```sql
-- Slow: each INSERT is its own transaction with fsync
INSERT INTO t VALUES (1);  -- implicit BEGIN, COMMIT, fsync
INSERT INTO t VALUES (2);  -- implicit BEGIN, COMMIT, fsync
INSERT INTO t VALUES (3);  -- implicit BEGIN, COMMIT, fsync

-- Fast: one transaction, one fsync
BEGIN;
INSERT INTO t VALUES (1);
INSERT INTO t VALUES (2);
INSERT INTO t VALUES (3);
COMMIT;  -- single fsync
```

### Transaction Types

```sql
BEGIN;               -- same as BEGIN DEFERRED
BEGIN DEFERRED;      -- default: acquire locks lazily
BEGIN IMMEDIATE;     -- acquire write lock immediately
BEGIN EXCLUSIVE;     -- acquire exclusive lock immediately
```

**DEFERRED (default):**
- No lock acquired until first database access
- First SELECT acquires a read lock
- First write statement attempts to upgrade to write lock
- If upgrade fails (another writer active), returns SQLITE_BUSY immediately
- busy_timeout does NOT apply to lock upgrades in DEFERRED mode

**IMMEDIATE:**
- Acquires write lock at BEGIN time
- If another writer is active, waits up to busy_timeout, then SQLITE_BUSY
- Benchmarks show approximately 2x better performance than DEFERRED for write-heavy workloads
- Recommended for any transaction that will write

**EXCLUSIVE:**
- Same as IMMEDIATE in WAL mode
- In rollback journal mode, also blocks readers
- Use only in rollback mode when you need total isolation

**Recommendation:** Use `BEGIN IMMEDIATE` for any transaction that will write. It fails fast at BEGIN time instead of failing mid-transaction after work has been done.

Sources: [SQLite Transaction Documentation](https://sqlite.org/lang_transaction.html), [SQLite Transactions (reorchestrate)](https://reorchestrate.com/posts/sqlite-transactions/)

### Batch Insert Performance

Transaction wrapping is the single most impactful optimization for inserts.

**Benchmarks (100M rows, Rust):**

| Technique | Time | Notes |
|-----------|------|-------|
| Naive single-row inserts (autocommit) | Minutes per million | Each row = separate transaction + fsync |
| Transaction-wrapped batches + prepared stmts | 34.3 seconds (100M rows) | Single connection |
| Threaded producer + single writer | 32.37 seconds (100M rows) | 4 worker threads, 1 writer |
| In-memory database | 29 seconds (100M rows) | ~2 seconds of disk I/O overhead |

**Impact of transaction wrapping by language (100M rows):**

| Language | Batched | Naive |
|----------|---------|-------|
| Rust (prepared + batched) | 34 seconds | N/A |
| PyPy (batched) | 2.5 minutes | N/A |
| CPython (batched) | 8.5 minutes | 10 minutes |

Source: [Fast SQLite Inserts (avi.im)](https://avi.im/blag/2021/fast-sqlite-inserts/)

**Impact by optimization technique:**

| Technique | Impact |
|-----------|--------|
| WAL + synchronous=NORMAL | Per-transaction overhead from 30ms+ to <1ms |
| Transaction wrapping | Write throughput 2-20x improvement |
| Prepared statements | Per-statement throughput up to 1.5x |
| Background WAL checkpoints | Eliminates occasional 30-100ms fsync spikes |

Source: [PowerSync SQLite Optimizations](https://www.powersync.com/blog/sqlite-optimizations-for-ultra-high-performance)

**PRAGMA settings for bulk loading (maximum speed, reduced safety):**

```sql
PRAGMA journal_mode = OFF;
PRAGMA synchronous = 0;
PRAGMA cache_size = 1000000;
PRAGMA locking_mode = EXCLUSIVE;
PRAGMA temp_store = MEMORY;
```

**Safe bulk loading (maintains crash safety):**

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  -- 64MB
PRAGMA temp_store = MEMORY;

BEGIN IMMEDIATE;
-- ... batch of inserts (100-10000 rows per transaction) ...
COMMIT;
```

**Optimal batch size:** 100-1,000 rows per transaction for general use. For bulk loading, larger batches (10K-100K) are better.

### Transaction Size Considerations

- Keep transactions as short as possible to minimize lock contention
- Very large transactions (multi-GB) can cause WAL growth and performance degradation
- In WAL mode, long-running read transactions prevent checkpointing, causing WAL bloat
- There is no hard limit on transaction size, but practical limits come from disk space for the WAL/journal

---

## 11. Query Optimization

### Reading EXPLAIN QUERY PLAN

```sql
EXPLAIN QUERY PLAN
SELECT o.id, c.name
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'active'
ORDER BY o.created_date DESC;
```

What to look for:
- `SCAN` = full table scan (often bad, check if index would help)
- `SEARCH` = index-assisted lookup (good)
- `COVERING INDEX` = all data from index, no table lookup (best)
- `USE TEMP B-TREE FOR ORDER BY` = sort step needed (index on ORDER BY columns could eliminate)
- `AUTOMATIC INDEX` = SQLite created a temporary index (permanent index would help)
- `CORRELATED SCALAR SUBQUERY` = runs for each outer row (rewrite as JOIN if possible)
- `MULTI-INDEX OR` = separate index lookups combined for OR conditions
- `CO-ROUTINE` = subquery evaluated in parallel, yielding single rows on demand
- `MATERIALIZE` = subquery result stored in temporary table

### Common Anti-Patterns

**1. Correlated subqueries instead of JOINs:**

```sql
-- BAD: subquery runs once per order row
SELECT o.id,
  (SELECT name FROM customers WHERE id = o.customer_id) AS customer_name
FROM orders o;

-- GOOD: single join operation
SELECT o.id, c.name
FROM orders o
JOIN customers c ON c.id = o.customer_id;
```

**2. UNION when UNION ALL suffices:**

```sql
-- BAD: sorts and deduplicates (unnecessary when sets are disjoint)
SELECT id, name FROM active_users
UNION
SELECT id, name FROM archived_users;

-- GOOD: just concatenates result sets
SELECT id, name FROM active_users
UNION ALL
SELECT id, name FROM archived_users;
```

UNION requires sorting all rows and comparing for duplicates. UNION ALL simply appends. For large datasets, UNION ALL can be 60%+ faster. Use UNION only when you genuinely need deduplication.

**3. Functions on indexed columns in WHERE:**

```sql
-- BAD: cannot use index on created_date
WHERE date(created_date) = '2024-01-15'

-- GOOD: preserves index usage
WHERE created_date >= '2024-01-15' AND created_date < '2024-01-16'

-- ALTERNATIVE: create an expression index
CREATE INDEX idx_date ON orders(date(created_date));
```

**4. OR conditions without supporting indexes:**

```sql
-- Potentially slow: needs indexes on BOTH columns
WHERE status = 'active' OR priority > 5

-- SQLite handles this with MULTI-INDEX OR if both columns are indexed
-- Without indexes on both, falls back to full table scan
```

**5. SELECT * when you only need specific columns:**

```sql
-- BAD: fetches all columns, prevents covering index optimization
SELECT * FROM orders WHERE status = 'active';

-- GOOD: may use covering index
SELECT id, customer_id FROM orders WHERE status = 'active';
```

**6. NOT IN with subqueries (NULL hazard):**

```sql
-- DANGEROUS: if subquery returns any NULL, entire NOT IN is NULL (returns no rows)
SELECT * FROM orders WHERE customer_id NOT IN (SELECT id FROM inactive_customers);

-- SAFE: NOT EXISTS handles NULLs correctly
SELECT * FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM inactive_customers ic WHERE ic.id = o.customer_id);
```

### Query Planner Optimizations to Know

**Automatic index creation:** When no persistent index helps and the lookup will run more than log(N) times during a statement, SQLite creates a temporary index. Construction cost is O(N log N). Watch for `AUTOMATIC INDEX` in EXPLAIN QUERY PLAN -- it means a permanent index would help.

**Subquery flattening:** SQLite attempts to merge subqueries in the FROM clause into the outer query, enabling index usage on the underlying tables instead of scanning a temporary result.

**Skip-scan:** When the leftmost index column has few distinct values but a later column is constrained, SQLite can skip-scan the index. Requires ANALYZE to have been run (needs statistics showing 18+ duplicates in the leftmost column).

**MIN/MAX optimization:** `SELECT MIN(col) FROM t` or `SELECT MAX(col) FROM t` on the leftmost column of an index executes as a single index lookup, not a full scan.

**Predicate push-down:** WHERE conditions from outer queries are pushed into subqueries to reduce the size of intermediate results.

**Constant propagation:** `WHERE a = b AND b = 5` implies `a = 5`, enabling SQLite to use an index on `a`.

**OR-to-IN conversion:** Multiple equality conditions on the same column separated by OR are rewritten as IN operators for index use: `WHERE x=1 OR x=2 OR x=3` becomes `WHERE x IN (1,2,3)`.

**LIKE/GLOB optimization:** When the pattern does not start with a wildcard and the column has BINARY collation, SQLite converts `LIKE 'prefix%'` to a range scan: `col >= 'prefix' AND col < 'prefiy'`.

### Running ANALYZE

```sql
-- Collect statistics for all tables:
ANALYZE;

-- Collect for a specific table:
ANALYZE orders;

-- Limit analysis time (rows examined per index):
PRAGMA analysis_limit = 1000;
ANALYZE;

-- View collected statistics:
SELECT * FROM sqlite_stat1;
```

Statistics are stored in `sqlite_stat1` (and optionally `sqlite_stat4`). The query planner uses these to estimate row counts and choose between competing index strategies. Without ANALYZE, the planner uses rough heuristics that may choose suboptimal plans.

Sources: [SQLite EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html), [SQLite Query Optimizer](https://sqlite.org/optoverview.html), [Deep Dive into SQLite Query Optimizer](https://micahkepe.com/blog/sqlite-query-optimizer/)

---

## 12. PRAGMA Settings for Production

### Recommended Production Configuration

Run these on every new connection:

```sql
-- Use write-ahead logging for concurrency and write speed
PRAGMA journal_mode = WAL;

-- NORMAL is safe in WAL mode; only checkpoints need fsync
PRAGMA synchronous = NORMAL;

-- 64MB page cache (negative value = kilobytes)
PRAGMA cache_size = -64000;

-- Memory-mapped I/O: let OS manage page caching (256MB)
PRAGMA mmap_size = 268435456;

-- Keep temp tables and indexes in memory
PRAGMA temp_store = MEMORY;

-- Wait 5 seconds on lock contention before returning SQLITE_BUSY
PRAGMA busy_timeout = 5000;

-- Enforce foreign key constraints (off by default)
PRAGMA foreign_keys = ON;
```

### PRAGMA Reference

**journal_mode = WAL**
- Enables concurrent readers + single writer
- Sequential writes, fewer fsync calls
- Persists across connections (set once, stored in database header)
- Cannot use on network file systems

**synchronous = NORMAL**
- Default is FULL (fsync every commit)
- NORMAL: only checkpoint fsyncs; safe in WAL mode against corruption
- Risk: committed transaction could roll back on power loss (not application crash)
- OFF: no fsync at all; corruption risk on any crash

**cache_size = -64000**
- Negative value = kilobytes; positive value = pages
- Default is -2000 (approximately 2MB)
- More cache = fewer disk reads, but may duplicate OS page cache
- Session-only; resets on each new connection

**mmap_size = 268435456**
- Enables memory-mapped I/O (fewer syscalls)
- Set to 0 to disable, or to expected database size
- On 64-bit systems, can set very large (e.g., 30GB) -- reserves virtual address space, not physical RAM
- Beneficial for read-heavy workloads

**temp_store = MEMORY**
- Temp tables, indexes, and intermediate results stored in RAM
- Faster than disk-based temp storage
- Value 2 = memory; value 1 = file; value 0 = compile-time default

**busy_timeout = 5000**
- Milliseconds to wait on lock contention before returning SQLITE_BUSY
- Without this, SQLITE_BUSY returns immediately
- Essential for any multi-connection setup

**foreign_keys = ON**
- Off by default (historical reasons)
- Negligible performance impact
- Must be set per-connection (not stored in database)

### For New Databases (SQLite 3.37.0+)

```sql
CREATE TABLE items (
    item_id INTEGER PRIMARY KEY,
    name    TEXT NOT NULL,
    price   REAL NOT NULL
) STRICT;
```

STRICT enforces column types at insert/update time, raising `SQLITE_CONSTRAINT_DATATYPE` on type mismatches.

### Maintenance PRAGMAs

```sql
-- For long-lived connections, run on open:
PRAGMA optimize = 0x10002;

-- Run periodically (hourly for long-lived connections):
PRAGMA optimize;

-- Run before closing short-lived connections:
PRAGMA optimize;
PRAGMA wal_checkpoint(PASSIVE);

-- Limit ANALYZE time (set before PRAGMA optimize):
PRAGMA analysis_limit = 400;

-- Limit WAL file size on disk:
PRAGMA journal_size_limit = 6144000;  -- 6MB
```

**PRAGMA optimize** collects statistics for tables where the query planner would have benefited from better data. The `0x10002` mask checks all tables and limits runtime. Run it:
- On connection open for long-lived apps (with `0x10002`)
- Before connection close for short-lived apps (plain `optimize`)
- After schema changes

**auto_vacuum:**

```sql
-- Must be set before creating any tables:
PRAGMA auto_vacuum = INCREMENTAL;

-- Then periodically:
PRAGMA incremental_vacuum;
```

- NONE (default): unused pages stay allocated; requires manual VACUUM
- FULL: automatic but can worsen fragmentation
- INCREMENTAL: you control when space is reclaimed

**VACUUM** rewrites the entire database. Avoid for databases over 100MB due to the time and temporary disk space required.

### Configuration Summary Table

| PRAGMA | Production Value | Default | Impact |
|--------|-----------------|---------|--------|
| journal_mode | WAL | DELETE | Concurrency, write speed |
| synchronous | NORMAL | FULL | Write speed (2-50x) |
| cache_size | -64000 | -2000 | Read speed for large DBs |
| mmap_size | 268435456 | 0 | Read speed, fewer syscalls |
| temp_store | MEMORY | DEFAULT | Temp operation speed |
| busy_timeout | 5000 | 0 | Prevents immediate BUSY errors |
| foreign_keys | ON | OFF | Data integrity |
| wal_autocheckpoint | 1000 | 1000 | WAL size vs checkpoint frequency |
| journal_size_limit | 6144000 | -1 (unlimited) | Disk space control |
| analysis_limit | 400 | 0 (unlimited) | ANALYZE/optimize runtime |

### Quick Reference: Connection Setup Template

```sql
-- Run on every new connection:
PRAGMA journal_mode = WAL;          -- persists in DB, but safe to re-set
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;
PRAGMA mmap_size = 268435456;
PRAGMA temp_store = MEMORY;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;
PRAGMA optimize = 0x10002;          -- for long-lived connections

-- Run periodically (hourly for long-lived connections):
PRAGMA optimize;

-- Run before closing short-lived connections:
PRAGMA optimize;
PRAGMA wal_checkpoint(PASSIVE);
```

Sources: [SQLite PRAGMA Documentation](https://sqlite.org/pragma.html), [SQLite PRAGMA Cheatsheet](https://cj.rs/blog/sqlite-pragma-cheatsheet-for-performance-and-consistency/), [SQLite Performance Tuning (phiresky)](https://phiresky.github.io/blog/2020/sqlite-performance-tuning/), [High Performance SQLite Recommended PRAGMAs](https://highperformancesqlite.com/articles/sqlite-recommended-pragmas), [SQLite Optimizations For Ultra High-Performance](https://www.powersync.com/blog/sqlite-optimizations-for-ultra-high-performance), [Write-Ahead Logging](https://sqlite.org/wal.html)

---

