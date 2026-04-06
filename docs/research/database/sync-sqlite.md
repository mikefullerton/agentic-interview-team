---
title: "SQLite Sync Implementation"
domain: database
type: guideline
status: draft
created: 2026-04-03
modified: 2026-04-06
author: Mike Fullerton
summary: "SQLite-specific sync implementation: schema design for sync, type mapping between SQLite and server databases, sync tools and extensions, and performance considerations"
platforms:
  - sqlite
tags:
  - database
  - sqlite
  - sync
  - offline-first
references:
  - https://sqlite.org/sessionintro.html
  - https://sqlite.org/datatype3.html
  - https://electric-sql.com
  - https://www.powersync.com
  - https://turso.tech
  - https://litestream.io
  - https://vlcn.io/docs/cr-sqlite
related:
  - sync-strategies.md
  - sync-case-studies.md
  - decision-frameworks.md
---

# SQLite Sync Implementation

> SQLite-specific sync implementation details: schema design for sync-ready tables, type mapping between SQLite and server databases, sync tools and extensions, and performance tuning for sync workloads.

---

## 20. Schema Design for Sync

### 20.1 UUID vs Integer Primary Keys

**Why UUIDs are necessary for offline-first sync:**

Auto-incrementing integers are generated locally by each device. When two devices create records offline, their local databases produce identical IDs. On sync, these duplicates cause conflicts, data corruption, or sync failures. UUIDs solve this by enabling client-side ID generation without server coordination.

**SQLite-specific advantage:** Unlike MySQL or PostgreSQL where random UUIDs fragment the clustered B-tree index, SQLite uses the internal `rowid` as its clustered index. A TEXT UUID primary key creates a separate B-tree index, so UUID randomness does not cause the same page-split fragmentation problems.

**Recommended: UUIDv7 (time-ordered)**

UUIDv7 includes a timestamp prefix, making IDs roughly ordered by creation time. This preserves the insert-order performance benefits of integers while maintaining global uniqueness. UUIDv7 is supported natively in PostgreSQL 17+ via `uuid_generate_v7()`.

```sql
-- SQLite: sync-ready table with TEXT UUID primary key
CREATE TABLE tasks (
    id TEXT PRIMARY KEY NOT NULL,         -- UUIDv7, generated client-side
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,             -- ISO-8601 UTC
    updated_at TEXT NOT NULL,             -- ISO-8601 UTC
    version INTEGER NOT NULL DEFAULT 1,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    last_synced_at TEXT                   -- NULL until first sync
);
```

```sql
-- PostgreSQL: corresponding server table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    version INTEGER NOT NULL DEFAULT 1,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    last_synced_at TIMESTAMPTZ
);
```

**Pitfalls to avoid:**
- Never use `INTEGER PRIMARY KEY AUTOINCREMENT` for synced tables -- IDs will collide across devices
- Never use `datetime('now')` as an ID substitute -- insufficient precision for uniqueness
- If using the sqlite-sync extension, use `cloudsync_uuid()` which generates UUIDv7 natively

**Sources:**
- [UUID vs Auto Increment for Primary Keys (Bytebase)](https://www.bytebase.com/blog/choose-primary-key-uuid-or-auto-increment/)
- [Primary Key Data Types (High Performance SQLite)](https://highperformancesqlite.com/watch/primary-key-data-types)
- [Android Room UUID Primary Key (CodeStudy)](https://www.codestudy.net/blog/using-uuid-for-primary-key-using-room-with-android/)

### 20.2 Timestamps for Change Tracking

Every synced table needs timestamps to detect what changed since the last sync.

**Required columns:**

| Column | Purpose | Format |
|--------|---------|--------|
| `created_at` | Record creation time | ISO-8601 UTC |
| `updated_at` | Last modification time | ISO-8601 UTC |
| `last_synced_at` | Last successful server sync | ISO-8601 UTC, NULL until synced |

**Detecting unsynced changes:**

```sql
-- Find all records that changed since last sync
SELECT * FROM tasks
WHERE last_synced_at IS NULL
   OR updated_at > last_synced_at;
```

**Automatic timestamp updates via triggers:**

```sql
CREATE TRIGGER tasks_update_timestamp
AFTER UPDATE ON tasks
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at  -- prevent infinite recursion
BEGIN
    UPDATE tasks SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE id = NEW.id;
END;
```

**Physical clocks vs logical clocks:**

Physical timestamps (`datetime('now')`) are simple but vulnerable to clock skew between devices. For systems where ordering correctness matters, consider:

- **Lamport timestamps:** Simple incrementing counter. Guarantees `e happened before f => L(e) < L(f)`, but the converse is not true. Low overhead but no concurrency detection.
- **Vector clocks:** Array of counters, one per device. Can distinguish "happened-before" from "concurrent" events. Space grows with O(n) where n = number of devices. Impractical for many-device scenarios.
- **Hybrid Logical Clocks (HLC):** Combine physical wall-clock time with a logical counter in a single 64-bit value. Remain close to wall-clock time while guaranteeing causal ordering. Strictly monotonic per-node. Self-stabilizing against NTP corrections. Recommended for most sync systems.

```
HLC timestamp = [48-bit physical time] + [16-bit logical counter]
```

**Sources:**
- [Handling Timestamps in SQLite (sqlite.ai)](https://blog.sqlite.ai/handling-timestamps-in-sqlite)
- [Hybrid Logical Clocks (Sergei Turukin)](https://sergeiturukin.com/2017/06/26/hybrid-logical-clocks.html)
- [Vector Clocks (Wikipedia)](https://en.wikipedia.org/wiki/Vector_clock)
- [Evolving Clock Sync in Distributed Databases (YugabyteDB)](https://www.yugabyte.com/blog/evolving-clock-sync-for-distributed-databases/)

### 20.3 Soft Deletes vs Hard Deletes (Tombstone Patterns)

Hard deleting a record on one device makes it impossible to propagate that deletion to other devices or the server -- there is no record left to sync. Sync systems require soft deletes.

**Simple soft delete:**

```sql
-- Mark as deleted instead of DELETE FROM
UPDATE tasks
SET is_deleted = 1,
    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
WHERE id = ?;
```

```sql
-- All normal queries exclude deleted records
SELECT * FROM tasks WHERE is_deleted = 0;
```

```sql
-- Sync queries include deleted records
SELECT * FROM tasks
WHERE last_synced_at IS NULL OR updated_at > last_synced_at;
```

**Index for filtering deleted records:**

```sql
CREATE INDEX idx_tasks_is_deleted ON tasks(is_deleted);
```

**Tombstone table pattern (alternative):**

Instead of a flag column, move deleted records to a separate tombstone table. This keeps the live table clean and fast while preserving deletion history for sync.

```sql
CREATE TABLE tasks_tombstones (
    id TEXT PRIMARY KEY NOT NULL,
    table_name TEXT NOT NULL,
    deleted_at TEXT NOT NULL,
    synced INTEGER NOT NULL DEFAULT 0
);

-- Trigger to capture deletes
CREATE TRIGGER tasks_soft_delete
BEFORE DELETE ON tasks
BEGIN
    INSERT INTO tasks_tombstones (id, table_name, deleted_at)
    VALUES (OLD.id, 'tasks', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));
END;
```

**Purging tombstones:**

Tombstones accumulate forever unless pruned. Only purge after confirming all devices have synced past the deletion:

```sql
-- Purge tombstones older than 90 days that have been synced
DELETE FROM tasks_tombstones
WHERE synced = 1
  AND deleted_at < strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-90 days');
```

**Pitfalls:**
- Never hard-delete records that other devices might still reference
- Always include `is_deleted` in indexes used by sync queries
- Plan a tombstone purge strategy from the start -- unbounded tombstones degrade performance

**Sources:**
- [Soft Deletes (Brent Ozar)](https://www.brentozar.com/archive/2020/02/what-are-soft-deletes-and-how-are-they-implemented/)
- [Tombstone Design Pattern (James Tharpe)](https://www.jamestharpe.com/tombstone-pattern/)
- [Soft Deletes (DoltHub)](https://www.dolthub.com/blog/2022-11-03-soft-deletes/)

### 20.4 Schema Compatibility Between SQLite and Server DB

SQLite's dynamic type system differs fundamentally from PostgreSQL/MySQL's rigid type system. Design schemas for compatibility.

**Key differences:**

| Concept | SQLite | PostgreSQL |
|---------|--------|------------|
| Type enforcement | Column affinity (recommended, not enforced) | Strict type enforcement |
| Boolean | INTEGER (0/1) | BOOLEAN (true/false) |
| Date/Time | TEXT (ISO-8601), INTEGER (unix), or REAL (julian) | TIMESTAMP, TIMESTAMPTZ, DATE, TIME |
| UUID | TEXT | UUID (native type) |
| JSON | TEXT with json1 functions | JSONB (binary, indexed) |
| BLOB | BLOB | BYTEA |
| Auto-increment | INTEGER PRIMARY KEY (alias for rowid) | SERIAL / GENERATED ALWAYS AS IDENTITY |

**Compatibility rules for sync schemas:**

1. Store booleans as INTEGER 0/1 in SQLite; map to BOOLEAN on server
2. Store dates as ISO-8601 TEXT in SQLite; map to TIMESTAMPTZ on server
3. Store UUIDs as TEXT in SQLite; map to UUID type on server
4. Store JSON as TEXT in SQLite; map to JSONB on server
5. Always use UTC for all timestamps on both sides
6. Define column constraints identically on both sides (NOT NULL, DEFAULT, CHECK)

**Sources:**
- [SQLite Data Types (w3resource)](https://www.w3resource.com/sqlite/sqlite-data-types.php)
- [SQLite Datatypes (sqlite.org)](https://www.sqlite.org/datatype3.html)
- [SQLAlchemy Type Hierarchy](https://docs.sqlalchemy.org/en/20/core/type_basics.html)

### 20.5 Version Columns for Optimistic Concurrency

A `version` column enables detecting concurrent modifications without timestamps.

**How it works:**

1. Client reads record with `version = 3`
2. Client modifies record locally, increments to `version = 4`
3. Client sends update to server: `UPDATE tasks SET ... WHERE id = ? AND version = 3`
4. If another client already incremented to `version = 4`, the WHERE clause matches zero rows
5. Server responds with conflict; client must reconcile

```sql
-- SQLite: version-based update
UPDATE tasks
SET title = ?,
    status = ?,
    version = version + 1,
    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
WHERE id = ? AND version = ?;
-- Check changes() == 1; if 0, conflict occurred
```

**SQLite-specific rowversion simulation:**

SQLite lacks a native auto-updating rowversion type. Simulate with a trigger:

```sql
-- Randomized version token (alternative to incrementing integer)
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    row_version BLOB NOT NULL DEFAULT (randomblob(8)),
    -- ... other columns
);

CREATE TRIGGER tasks_rowversion
AFTER UPDATE ON tasks
BEGIN
    UPDATE tasks SET row_version = randomblob(8) WHERE id = NEW.id;
END;
```

**Best practice:** Use both `version` (integer) and `updated_at` (timestamp). The version integer is authoritative for conflict detection; the timestamp is useful for debugging and human-readable ordering.

**Sources:**
- [Optimistic Concurrency (ServiceStack)](https://docs.servicestack.net/ormlite/optimistic-concurrency)
- [Handling Concurrency Conflicts (EF Core)](https://learn.microsoft.com/en-us/ef/core/saving/concurrency)
- [Entity Framework Core: SQLite Concurrency Checks](https://elanderson.net/2018/12/entity-framework-core-sqlite-concurrency-checks/)

---
## 24. Type Mapping Between SQLite and Server Databases

### 24.1 Complete Type Mapping Reference

| Data Concept | SQLite Storage | SQLite DDL | PostgreSQL | MySQL | SQL Server |
|-------------|---------------|------------|------------|-------|------------|
| UUID | TEXT | `id TEXT PRIMARY KEY` | `UUID` | `CHAR(36)` | `UNIQUEIDENTIFIER` |
| Boolean | INTEGER | `is_active INTEGER DEFAULT 0` | `BOOLEAN` | `TINYINT(1)` | `BIT` |
| Timestamp (UTC) | TEXT | `created_at TEXT` | `TIMESTAMPTZ` | `DATETIME` | `DATETIMEOFFSET` |
| Date only | TEXT | `birth_date TEXT` | `DATE` | `DATE` | `DATE` |
| Integer | INTEGER | `count INTEGER` | `INTEGER` / `BIGINT` | `INT` / `BIGINT` | `INT` / `BIGINT` |
| Decimal | TEXT or REAL | `price TEXT` | `NUMERIC(10,2)` | `DECIMAL(10,2)` | `DECIMAL(10,2)` |
| Float | REAL | `latitude REAL` | `DOUBLE PRECISION` | `DOUBLE` | `FLOAT` |
| Short text | TEXT | `name TEXT` | `VARCHAR(255)` | `VARCHAR(255)` | `NVARCHAR(255)` |
| Long text | TEXT | `description TEXT` | `TEXT` | `TEXT` | `NVARCHAR(MAX)` |
| JSON | TEXT | `metadata TEXT` | `JSONB` | `JSON` | `NVARCHAR(MAX)` |
| Binary data | BLOB | `avatar BLOB` | `BYTEA` | `LONGBLOB` | `VARBINARY(MAX)` |
| Enum | TEXT | `status TEXT CHECK(...)` | `VARCHAR` + CHECK | `ENUM(...)` | `VARCHAR` + CHECK |

### 24.2 Date/Time Format Alignment

**Critical rule: Always store and transmit dates as ISO-8601 UTC strings.**

```sql
-- SQLite: store as ISO-8601 TEXT
INSERT INTO events (id, event_date)
VALUES ('evt-1', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));
-- Result: '2026-04-03T14:30:45.123Z'

-- PostgreSQL: parse from ISO-8601
INSERT INTO events (id, event_date)
VALUES ('evt-1', '2026-04-03T14:30:45.123Z'::timestamptz);
```

**Conversion helpers:**

```sql
-- SQLite: ISO-8601 TEXT to Unix timestamp
SELECT strftime('%s', '2026-04-03T14:30:45Z');  -- 1775148645

-- SQLite: Unix timestamp to ISO-8601 TEXT
SELECT strftime('%Y-%m-%dT%H:%M:%fZ', 1775148645, 'unixepoch');

-- SQLite: Compare dates stored as TEXT (works because ISO-8601 is lexicographically sortable)
SELECT * FROM events WHERE event_date > '2026-01-01T00:00:00Z';
```

**Pitfalls:**
- SQLite has no TIMESTAMP type -- it stores dates as TEXT, REAL, or INTEGER
- ISO-8601 TEXT comparison requires consistent formatting (always use leading zeros, always include 'Z' suffix)
- Never mix timestamp formats in the same column
- Always convert to UTC before storing; convert to local time only at the display layer
- PostgreSQL `TIMESTAMP` (without time zone) and `TIMESTAMPTZ` behave differently -- always use `TIMESTAMPTZ` for synced data

### 24.3 JSON Handling Differences

```sql
-- SQLite: JSON stored as TEXT, queried with json1 functions
SELECT json_extract(metadata, '$.color') FROM tasks WHERE id = ?;
SELECT metadata ->> 'color' FROM tasks WHERE id = ?;  -- SQLite 3.38+

-- PostgreSQL: JSON stored as JSONB (binary, indexed)
SELECT metadata->>'color' FROM tasks WHERE id = ?;

-- SQLite: index on JSON field
CREATE INDEX idx_tasks_color ON tasks(json_extract(metadata, '$.color'));

-- PostgreSQL: GIN index on JSONB
CREATE INDEX idx_tasks_metadata ON tasks USING GIN (metadata);
```

**Compatibility notes:**
- SQLite's `->` and `->>` operators are designed to be compatible with both MySQL and PostgreSQL syntax
- SQLite JSONB format is NOT binary-compatible with PostgreSQL JSONB -- it is a different on-disk format
- Always validate JSON on both sides -- SQLite's json1 returns NULL for invalid JSON, PostgreSQL raises an error

### 24.4 Boolean Handling

```sql
-- SQLite: booleans are integers
INSERT INTO tasks (id, is_complete) VALUES ('task-1', 0);
SELECT * FROM tasks WHERE is_complete = 1;

-- PostgreSQL: native boolean
INSERT INTO tasks (id, is_complete) VALUES ('task-1', FALSE);
SELECT * FROM tasks WHERE is_complete = TRUE;
```

**Sync conversion layer:**

```python
def sqlite_to_postgres(record):
    """Convert SQLite record to PostgreSQL-compatible values."""
    converted = dict(record)
    for col in boolean_columns:
        converted[col] = bool(converted[col])  # 0/1 -> False/True
    for col in timestamp_columns:
        # TEXT -> datetime object (PostgreSQL driver handles conversion)
        converted[col] = datetime.fromisoformat(converted[col])
    return converted

def postgres_to_sqlite(record):
    """Convert PostgreSQL record to SQLite-compatible values."""
    converted = dict(record)
    for col in boolean_columns:
        converted[col] = int(converted[col])  # True/False -> 1/0
    for col in timestamp_columns:
        converted[col] = record[col].isoformat()  # datetime -> TEXT
    return converted
```

**Sources:**
- [SQLite Data Types (w3resource)](https://www.w3resource.com/sqlite/sqlite-data-types.php)
- [Datatypes in SQLite (sqlite.org)](https://www.sqlite.org/datatype3.html)
- [Handling Timestamps in SQLite (sqlite.ai)](https://blog.sqlite.ai/handling-timestamps-in-sqlite)
- [Drizzle ORM SQLite Column Types](https://orm.drizzle.team/docs/column-types/sqlite)
- [Drizzle ORM PostgreSQL Column Types](https://orm.drizzle.team/docs/column-types/pg)

---
## 25. SQLite Sync Tools and Extensions

### 25.1 SQLite Session Extension (sqlite3session)

Built into SQLite. Records changes to attached tables and packages them as binary changesets.

**Key capabilities:**
- Captures INSERT, UPDATE, DELETE as binary blobs
- Changesets can be applied to other databases with the same schema
- Built-in conflict handler callback
- Supports changeset inversion (undo)
- Supports changeset concatenation (batch multiple sessions)

**Conflict handler callback types:**

| Conflict Type | Trigger Condition |
|--------------|-------------------|
| SQLITE_CHANGESET_DATA | UPDATE/DELETE: row exists but non-PK values don't match |
| SQLITE_CHANGESET_NOTFOUND | UPDATE/DELETE: no row with matching PK |
| SQLITE_CHANGESET_CONFLICT | INSERT: row with matching PK already exists |
| SQLITE_CHANGESET_CONSTRAINT | Change violates UNIQUE or CHECK constraint |

**Limitations:**
- Tables must have a declared PRIMARY KEY
- Virtual tables not supported
- NULL values in PK columns are ignored (rows not captured)
- Requires compile-time flags: `-DSQLITE_ENABLE_SESSION -DSQLITE_ENABLE_PREUPDATE_HOOK`

**Source:** [SQLite Session Extension (sqlite.org)](https://sqlite.org/sessionintro.html)

### 25.2 CR-SQLite (CRDT-Based Merge)

Run-time loadable extension that adds multi-master replication via CRDTs.

**Setup:**

```sql
.load crsqlite

CREATE TABLE documents (id TEXT PRIMARY KEY NOT NULL, title TEXT, content TEXT);
SELECT crsql_as_crr('documents');
```

**Sync between two databases:**

```sql
-- On Device A: export changes
SELECT * FROM crsql_changes WHERE db_version > ?;

-- On Device B: import Device A's changes
INSERT INTO crsql_changes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
```

**Schema changes on CRR tables:**

```sql
SELECT crsql_begin_alter('documents');
ALTER TABLE documents ADD COLUMN status TEXT;
SELECT crsql_commit_alter('documents');
```

**CRDT algorithms per column:** LWW (last-write-wins), fractional indices (list ordering), observe-remove sets (row presence). Counter and rich-text CRDTs in development.

**Source:** [cr-sqlite (GitHub)](https://github.com/vlcn-io/cr-sqlite)

### 25.3 Litestream

Streaming WAL-based replication for disaster recovery. Not a sync tool -- it replicates a single SQLite database to cloud storage (S3, Azure Blob, SFTP).

**How it works:**
1. Takes over SQLite's WAL checkpointing process
2. Starts a long-running read transaction to prevent other processes from checkpointing
3. Continuously copies new WAL pages to a "shadow WAL" directory
4. Streams shadow WAL to configured storage backends
5. Periodically takes full snapshots; prunes old WAL files

**Key configuration:**

```yaml
dbs:
  - path: /path/to/app.db
    replicas:
      - type: s3
        bucket: my-backup-bucket
        path: app.db
        retention: 72h
```

**Live read replicas:** Litestream can stream changes to read-only replicas on other servers, applying changes in a transactionally-safe manner.

**When to use:** Server-side SQLite backup and disaster recovery. Not designed for multi-writer sync or device-to-server sync.

**Source:** [Litestream (litestream.io)](https://litestream.io/how-it-works/)

### 25.4 ElectricSQL

Syncs Postgres with client-side SQLite using the Postgres logical replication WAL.

**Architecture:**
- Electric service sits between Postgres and clients
- Reads Postgres WAL via logical replication
- Streams changes to client-side SQLite (browser via WASM, mobile via native SQLite)
- Client writes go through Electric back to Postgres
- Conflict resolution via CRDTs (last-writer-wins semantics)

**Key characteristic:** "Direct-to-Postgres" -- writes bypass your application backend. Validation must happen via Postgres constraints and DDLX rules.

**Trade-offs:**
- Pro: No backend code needed for sync
- Con: Cannot inject custom business logic on the write path
- Con: Modifies Postgres schema (adds shadow tables, triggers)
- Con: Requires SUPERUSER database privileges

**Source:** [ElectricSQL Alternatives (electric-sql.com)](https://electric-sql.com/docs/reference/alternatives)

### 25.5 PowerSync

Postgres-to-SQLite sync engine with server-authoritative write path.

**Architecture:**
- PowerSync Service connects to Postgres via logical replication (read-only)
- Streams data to client-side SQLite based on configurable "Sync Rules"
- Client writes go to a local upload queue, then through YOUR backend
- Your backend applies business logic, validation, authorization
- Changes committed to Postgres flow back to all clients via PowerSync

**Key differentiator:** You control the write path. The server can reject, transform, or merge client writes with custom logic.

**Sync Rules (dynamic partial replication):**

```yaml
# Only sync tasks belonging to the current user
- table: tasks
  filter: "user_id = token_parameters.user_id"
```

**Consistency model:** Causal+ consistency via checkpoint-based synchronization. Clients update state atomically when receiving all data matching a checkpoint.

**Supported backends:** Postgres (GA), MongoDB (GA), MySQL (planned)

**Sources:**
- [PowerSync v1.0 (powersync.com)](https://www.powersync.com/blog/introducing-powersync-v1-0-postgres-sqlite-sync-layer)
- [ElectricSQL vs PowerSync (powersync.com)](https://www.powersync.com/blog/electricsql-vs-powersync)

### 25.6 Turso / libSQL

Fork of SQLite with built-in replication and embedded replicas.

**Embedded replicas architecture:**
- Source of truth is the remote Turso database
- Local SQLite copy on each device for zero-latency reads
- Sync uses frame-based WAL replication (1 frame = 4KB page)
- Guarantees read-your-writes semantics

**Sync strategies:**
- Manual sync: call `client.sync()` when desired
- Periodic sync: configure `syncInterval` for automatic polling
- Offline writes: write to local WAL, push when connected, pull to reconcile

**Conflict resolution options:**
- `FAIL_ON_CONFLICT` -- reject and require explicit handling
- `DISCARD_LOCAL` -- server-wins (discard local changes)
- `REBASE_LOCAL` -- replay local changes on top of server state
- `MANUAL_RESOLUTION` -- callback with `localData` and `remoteData`

```typescript
const client = createClient({
    url: 'local.db',
    syncUrl: 'libsql://remote.turso.io',
    authToken: '...',
});

await client.execute('INSERT INTO tasks VALUES (?)', ['task-1']);
await client.sync({ strategy: SyncStrategy.REBASE_LOCAL });
```

**Source:** [Turso Offline Writes (turso.tech)](https://turso.tech/blog/introducing-offline-writes-for-turso)

### 25.7 SQLite Sync (sqlite.ai)

CRDT-based extension that syncs SQLite with SQLite Cloud, PostgreSQL, and Supabase.

**Setup:**

```sql
.load cloudsync

-- Enable CRDT sync on a table
SELECT cloudsync_init('tasks');

-- Use UUIDv7 for primary keys
INSERT INTO tasks (id, title) VALUES (cloudsync_uuid(), 'New task');

-- Connect and sync
SELECT cloudsync_network_init('your-database-id');
SELECT cloudsync_network_set_apikey('your-api-key');
SELECT cloudsync_network_sync();
```

**CRDT algorithm options:**
- `cls` (Causal-Length Set) -- default
- `dws` (Delete-Wins Set)
- `aws` (Add-Wins Set)
- `gos` (Grow-Only Set)

**Block-level LWW for text columns:**

```sql
-- Enable per-line conflict resolution on a text column
SELECT cloudsync_set_column('notes', 'body', 'algo', 'block');
SELECT cloudsync_set_column('notes', 'body', 'delimiter', '\n');

-- After sync, materialize the merged text
SELECT cloudsync_text_materialize('notes', 'body', 'note-001');
```

**Schema requirements:**
- All NOT NULL columns must have DEFAULT values
- TEXT primary keys with UUIDv7 recommended
- Must call `cloudsync_begin_alter` / `cloudsync_commit_alter` before/after ALTER TABLE

**Source:** [sqlite-sync API (GitHub)](https://github.com/sqliteai/sqlite-sync/blob/main/API.md)

### Tool Comparison Matrix

| Feature | Session Extension | cr-sqlite | Litestream | ElectricSQL | PowerSync | Turso | sqlite-sync |
|---------|-------------------|-----------|------------|-------------|-----------|-------|-------------|
| **Sync direction** | Manual | Bidirectional | One-way (backup) | Bidirectional | Bidirectional | Bidirectional | Bidirectional |
| **Conflict resolution** | Callback | CRDT (automatic) | N/A | CRDT (LWW) | Custom (your backend) | Multiple strategies | CRDT (automatic) |
| **Server DB** | Any | Any | N/A (storage) | Postgres only | Postgres, MongoDB | Turso Cloud | SQLite Cloud, PG, Supabase |
| **Offline writes** | Yes | Yes | No | Yes | Yes | Yes | Yes |
| **Custom write logic** | Yes | No | N/A | No (PG constraints) | Yes (your backend) | Partial | No |
| **Setup complexity** | Low (C API) | Low (extension) | Low (config) | Medium | Medium | Low | Low (extension) |
| **Maturity** | Stable (part of SQLite) | Beta | Stable | Production | Production | Beta (offline) | Beta |

---
## 27. Performance Considerations for Sync

### 27.1 Batch Size for Sync Operations

**Recommendations:**

| Context | Batch Size | Rationale |
|---------|------------|-----------|
| Mobile (unstable network) | 50-100 records | Smaller batches survive connection drops |
| Desktop (stable network) | 500-1000 records | Larger batches reduce HTTP overhead |
| Initial bootstrap | 1000-5000 records | Fast initial sync is critical for UX |
| Background sync | 100-500 records | Balance throughput with UI responsiveness |

**JSON bulk operations (PowerSync pattern):**

```sql
-- Bulk insert via JSON: single statement, no parameter limit issues
INSERT INTO tasks (id, title, status)
SELECT e->>'id', e->>'title', e->>'status'
FROM json_each(?) e;

-- Bulk update via JSON
WITH data AS (
    SELECT e->>'id' AS id, e->>'title' AS title, e->>'status' AS status
    FROM json_each(?) e
)
UPDATE tasks
SET title = data.title, status = data.status
FROM data
WHERE tasks.id = data.id;

-- Bulk delete via JSON
DELETE FROM tasks
WHERE id IN (SELECT e.value FROM json_each(?) e);
```

### 27.2 Transaction Management During Sync

**Rule: Wrap each sync batch in a single transaction.**

```python
def apply_sync_batch(changes):
    db.execute("BEGIN IMMEDIATE")  # IMMEDIATE to acquire write lock upfront
    try:
        for change in changes:
            apply_change(db, change)
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise
```

**Why IMMEDIATE for sync transactions:** `BEGIN IMMEDIATE` acquires the write lock at the start of the transaction, not at the first write statement. This prevents SQLITE_BUSY errors mid-transaction, which would require rolling back and retrying the entire batch.

**Connection strategy:**
- Single write connection with an application-level queue (prevents SQLITE_BUSY)
- Multiple read connections for UI queries
- Never hold a write transaction open while waiting for network I/O

**Transaction batching benchmark:**
- Without transaction: each INSERT triggers an fsync (30ms+ per operation)
- With transaction wrapping: 2-20x throughput improvement
- WAL mode + synchronous=NORMAL: reduces per-transaction overhead from 30ms+ to under 1ms

### 27.3 Index Strategy for Sync Metadata Columns

**Essential indexes for sync:**

```sql
-- Find unsynced records (most important sync query)
CREATE INDEX idx_tasks_sync_status
ON tasks(last_synced_at, updated_at)
WHERE last_synced_at IS NULL OR updated_at > last_synced_at;

-- Outbox: find pending entries
CREATE INDEX idx_outbox_pending
ON outbox(status, next_attempt_at)
WHERE status = 'pending';

-- Change log: find unsynced changes
CREATE INDEX idx_changelog_unsynced
ON change_log(synced, changed_at)
WHERE synced = 0;

-- Soft-deleted records
CREATE INDEX idx_tasks_deleted ON tasks(is_deleted);

-- Version-based sync
CREATE INDEX idx_tasks_version ON tasks(version);
```

**Partial indexes (SQLite 3.8.0+) reduce index size:** Only index the rows that matter for sync queries.

**Use EXPLAIN QUERY PLAN to verify:**

```sql
EXPLAIN QUERY PLAN
SELECT * FROM tasks
WHERE last_synced_at IS NULL OR updated_at > last_synced_at;
-- Should show "SEARCH ... USING INDEX" not "SCAN"
```

### 27.4 WAL Mode Benefits for Concurrent Sync Reads/Writes

**Essential PRAGMA configuration for sync:**

```sql
PRAGMA journal_mode = WAL;           -- enable write-ahead logging
PRAGMA synchronous = NORMAL;         -- safe for app crashes, fast commits
PRAGMA busy_timeout = 5000;          -- wait 5s instead of failing immediately
PRAGMA journal_size_limit = 6144000; -- limit WAL file to ~6MB
PRAGMA cache_size = -2000;           -- 2MB page cache (negative = KB)
PRAGMA foreign_keys = ON;            -- enforce referential integrity
```

**WAL concurrency model:**
- Multiple readers can proceed simultaneously
- One writer at a time (SQLITE_BUSY if contended)
- Readers do not block writers
- Writers do not block readers
- Readers see a consistent snapshot from when they started

**WAL checkpoint management:**

```sql
-- Default: auto-checkpoint every 1000 pages
PRAGMA wal_autocheckpoint = 1000;

-- Manual checkpoint (run periodically or after large sync batches)
PRAGMA wal_checkpoint(PASSIVE);   -- doesn't block, checkpoints what it can
PRAGMA wal_checkpoint(TRUNCATE);  -- blocks briefly, resets WAL to zero size
```

**Checkpoint strategy for sync:**
- Use PASSIVE checkpoints during normal operation
- Use TRUNCATE checkpoint after large sync batches (reduces WAL file size)
- Run checkpoints in a separate thread/connection to avoid blocking UI reads

### 27.5 Database Size Management

**Monitoring database size:**

```sql
-- Total size and free space
SELECT page_count * page_size AS total_bytes,
       freelist_count * page_size AS free_bytes
FROM pragma_page_count(), pragma_page_size(), pragma_freelist_count();
```

**Pruning strategy:**

```sql
-- 1. Purge synced outbox entries (keep 7 days for debugging)
DELETE FROM outbox WHERE status = 'done'
  AND created_at < strftime('%s', 'now', '-7 days') * 1000;

-- 2. Purge old change log entries
DELETE FROM change_log WHERE synced = 1
  AND changed_at < strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-30 days');

-- 3. Hard-delete confirmed tombstones
DELETE FROM tasks WHERE is_deleted = 1
  AND last_synced_at IS NOT NULL
  AND updated_at < strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-90 days');

-- 4. Reclaim space (only if significant free space exists)
PRAGMA incremental_vacuum(500);  -- free up to 500 pages
```

**When to VACUUM:**
- After deleting 25%+ of database content
- Run during app idle time or on app launch
- VACUUM locks the database and requires 2x the database size in free disk space
- Prefer `PRAGMA incremental_vacuum` for gradual, non-blocking reclamation

**Sources:**
- [SQLite Optimizations for Ultra High-Performance (PowerSync)](https://www.powersync.com/blog/sqlite-optimizations-for-ultra-high-performance)
- [Best Practices for SQLite Performance (Android Developers)](https://developer.android.com/topic/performance/sqlite-performance-best-practices)
- [Write-Ahead Logging (sqlite.org)](https://sqlite.org/wal.html)
- [SQLite Performance Tuning (phiresky)](https://phiresky.github.io/blog/2020/sqlite-performance-tuning/)
- [SQLite WAL Mode for Mobile Apps (DEV)](https://dev.to/software_mvp-factory/sqlite-wal-mode-and-connection-strategies-for-high-throughput-mobile-apps-beyond-the-basics-eh0)

---
