---

id: AB416D40-2688-4531-95FB-613F0D2FA8CF
title: "Transactions and Concurrency"
domain: agentic-cookbook://guidelines/implementing/data/transactions-and-concurrency
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Rules for transaction management and concurrency in SQLite, covering WAL mode, journal mode selection, BEGIN IMMEDIATE vs DEFERRED, connection strategies, busy_timeout, PRAGMA tuning, and WAL benefits for sync workloads."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - transactions
  - concurrency
  - wal
  - performance
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
  - guidelines/data/access-pattern-analysis.md
references:
  - https://sqlite.org/wal.html
  - https://sqlite.org/lang_transaction.html
  - https://sqlite.org/pragma.html
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - concurrency
---

# Transactions and Concurrency

Transaction management is the single most impactful performance lever in SQLite. Individual autocommit inserts each pay a full fsync — wrapping them in explicit transactions reduces that cost to one fsync per batch. WAL mode unlocks concurrent reads alongside writes and cuts per-commit overhead from 30ms+ to under 1ms.

## Use WAL Mode by Default

MUST enable WAL mode for any application with concurrent reads, or where write latency matters.

```sql
PRAGMA journal_mode = WAL;
```

WAL (Write-Ahead Log) changes the write mechanism: instead of modifying the database file directly, SQLite appends changes to a separate `-wal` file. The original database stays intact until a checkpoint transfers changes back.

**Concurrency model:**
- Unlimited simultaneous readers
- One writer at a time
- Readers do not block writers; writers do not block readers
- Each reader sees a consistent snapshot from transaction start

**Performance advantages over rollback journal modes:**
- Writes are sequential (append-only), not random I/O
- Fewer `fsync()` calls — a COMMIT appends a commit record, no database-file fsync required
- With `synchronous = NORMAL`, per-transaction overhead drops from 30ms+ to under 1ms

**Limitations:**
- All processes must share the same physical machine (shared memory requirement)
- Cannot change `page_size` after enabling WAL
- Adds `-wal` and `-shm` files alongside the database
- Cannot use on network file systems

WAL mode persists in the database header — it survives reconnects. Set it once per database, but re-setting it on connection open is safe and recommended.

## Journal Mode Selection

| Mode | Concurrent Reads | Write Speed | Durability | Use When |
|------|-----------------|-------------|------------|----------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| WAL | Yes | Fast (sequential) | Full (with NORMAL) | Default for most apps |
| DELETE | No | Slow | Full | Network file systems, max compatibility |
| MEMORY | No | Fast | None | Ephemeral/rebuildable data only |
| OFF | No | Fastest | None | Bulk load where crash safety is irrelevant |

MUST NOT use `MEMORY` or `OFF` journal modes in production databases where data loss on crash is unacceptable.

## Explicit Transactions — Always

Every SQL statement runs in a transaction. Without an explicit `BEGIN`, each statement gets its own implicit transaction with a separate fsync.

```sql
-- SLOW: each INSERT triggers an fsync (30ms+ per statement)
INSERT INTO t VALUES (1);
INSERT INTO t VALUES (2);
INSERT INTO t VALUES (3);

-- FAST: one fsync for all three
BEGIN;
INSERT INTO t VALUES (1);
INSERT INTO t VALUES (2);
INSERT INTO t VALUES (3);
COMMIT;
```

MUST wrap batches of writes in explicit transactions. Even a modest batch (10–100 rows) benefits significantly.

**Optimal batch size:**
- General use: 100–1,000 rows per transaction
- Bulk loading: 10,000–100,000 rows per transaction
- Sync batches: 50–500 records (smaller on unstable networks)

## BEGIN IMMEDIATE vs DEFERRED

```sql
BEGIN;              -- same as BEGIN DEFERRED
BEGIN DEFERRED;     -- default: acquire locks lazily
BEGIN IMMEDIATE;    -- acquire write lock at BEGIN time
BEGIN EXCLUSIVE;    -- exclusive lock (equivalent to IMMEDIATE in WAL mode)
```

**DEFERRED** acquires no lock until first access. The first write statement then attempts to upgrade from a read lock to a write lock. If another writer is active, this upgrade fails immediately — `busy_timeout` does NOT apply to lock upgrades in DEFERRED mode. Work done before the failed upgrade is lost and must be retried.

**IMMEDIATE** acquires the write lock at `BEGIN` time. If another writer is active, SQLite waits up to `busy_timeout` milliseconds before returning `SQLITE_BUSY`. Benchmarks show approximately 2x better throughput than DEFERRED for write-heavy workloads.

MUST use `BEGIN IMMEDIATE` for any transaction that will write. It fails fast at `BEGIN` time rather than mid-transaction after work has been done.

```sql
-- Correct pattern for write transactions
BEGIN IMMEDIATE;
INSERT INTO tasks ...;
UPDATE tasks SET ...;
COMMIT;
```

## busy_timeout — Always Set It

Without `busy_timeout`, any lock contention returns `SQLITE_BUSY` immediately. This causes needless errors and retry storms in multi-connection setups.

```sql
PRAGMA busy_timeout = 5000;  -- wait up to 5 seconds before returning BUSY
```

MUST set `busy_timeout` on every connection in any multi-connection or concurrent access scenario. A value of 5000ms (5 seconds) is a safe default. Set it lower (500–1000ms) for interactive UI operations where a 5-second wait would be visible to the user.

## Recommended PRAGMA Configuration

Set these on every new connection:

```sql
PRAGMA journal_mode = WAL;       -- concurrent reads + fast sequential writes
PRAGMA synchronous = NORMAL;     -- safe in WAL mode; only checkpoints fsync
PRAGMA cache_size = -64000;      -- 64MB page cache (negative value = KB)
PRAGMA mmap_size = 268435456;    -- 256MB memory-mapped I/O
PRAGMA temp_store = MEMORY;      -- temp tables and indexes in RAM
PRAGMA busy_timeout = 5000;      -- wait 5s on lock contention
PRAGMA foreign_keys = ON;        -- enforce referential integrity
PRAGMA optimize = 0x10002;       -- update query planner stats (long-lived connections)
```

**synchronous = NORMAL** in WAL mode: checkpoints fsync to disk, but individual commits do not. This is safe against application crashes. The only risk is a committed transaction rolling back on sudden power loss — acceptable for most use cases.

**cache_size** is session-only; it resets on each connection. 64MB is a good starting point for applications with larger working sets.

**mmap_size** enables memory-mapped I/O, reducing syscall overhead on read-heavy workloads. On 64-bit systems, setting this to the expected database size reserves virtual address space without consuming physical RAM.

## Connection Strategy

**Single writer, multiple readers:**
- One dedicated write connection with an application-level queue
- Multiple read connections for concurrent UI or background queries
- Never hold a write transaction open while waiting for network I/O

```python
# Sync workload pattern
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

MUST NOT open the write lock and then wait on external I/O (network requests, user input). Keep write transactions short.

## WAL Checkpointing

WAL content must be periodically transferred back to the main database file. By default, SQLite checkpoints automatically when the WAL reaches 1,000 pages.

```sql
PRAGMA wal_checkpoint(PASSIVE);   -- non-blocking; checkpoints what it can
PRAGMA wal_checkpoint(FULL);      -- blocks new writers until complete
PRAGMA wal_checkpoint(TRUNCATE);  -- blocks briefly; resets WAL to zero bytes
```

SHOULD run `PRAGMA wal_checkpoint(PASSIVE)` periodically during normal operation. After large sync batches, use `TRUNCATE` to reclaim WAL disk space.

SHOULD cap WAL file size to prevent unbounded growth:

```sql
PRAGMA journal_size_limit = 6144000;  -- limit WAL to ~6MB
```

Three causes of WAL growth to avoid:
1. Auto-checkpointing disabled without a manual replacement
2. Long-running read transactions that prevent checkpoint completion
3. Very large write transactions that block the checkpoint

Run checkpoints in a separate thread or connection so they do not block foreground reads.

## WAL Benefits for Sync Workloads

Sync operations write in bursts (a batch of changes arrives, gets applied, then the connection idles). WAL mode is well-suited to this pattern:

- Readers continue to serve UI queries while the sync write transaction runs
- Sequential WAL appends are faster than random writes into the main database file
- `BEGIN IMMEDIATE` on the sync writer prevents mid-batch lock failures
- After a large batch, a `TRUNCATE` checkpoint resets WAL size without blocking readers for long

For concurrent sync read/write access, WAL mode with a single write connection and a `busy_timeout` of 5,000ms eliminates nearly all `SQLITE_BUSY` errors in practice.

## Bulk Load Configuration (Reduced Safety)

For one-time bulk loads where crash safety during the load is acceptable:

```sql
PRAGMA journal_mode = OFF;
PRAGMA synchronous = 0;
PRAGMA cache_size = 1000000;
PRAGMA locking_mode = EXCLUSIVE;
PRAGMA temp_store = MEMORY;
```

Restore safe settings immediately after the bulk load completes. MUST NOT use these settings in production code paths.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
