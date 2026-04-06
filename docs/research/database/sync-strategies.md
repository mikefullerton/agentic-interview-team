---
title: "Sync Strategies"
domain: database
type: guideline
status: draft
created: 2026-04-06
modified: 2026-04-06
author: Mike Fullerton
summary: "Database-agnostic sync strategies: conflict resolution patterns, sync protocols, offline-first architecture, and local-remote synchronization approaches"
tags:
  - database
  - sync
  - offline-first
  - conflict-resolution
references:
  - https://sergeiturukin.com/2017/06/26/hybrid-logical-clocks.html
  - https://en.wikipedia.org/wiki/Vector_clock
  - https://crdt.tech/implementations
  - https://thom.ee/blog/crdt-vs-operational-transformation/
  - https://www.milanjovanovic.tech/blog/implementing-the-outbox-pattern
  - https://microservices.io/patterns/data/transactional-outbox.html
related:
  - sync-sqlite.md
  - sync-case-studies.md
  - decision-frameworks.md
---

# Sync Strategies

> Database-agnostic sync strategies for local-remote synchronization: conflict resolution patterns, sync protocols, offline-first architecture, and practical implementation guidance.
> Research compiled April 2026 from practitioner sources, academic references, and production system analysis.

---

## Table of Contents

1. [Conflict Resolution](#1-conflict-resolution)
2. [Sync Protocols and Patterns](#2-sync-protocols-and-patterns)
3. [Offline-First Architecture](#3-offline-first-architecture)
4. [Clock Systems and Ordering](#4-clock-systems-and-ordering)
5. [Sync Engine Design](#5-sync-engine-design)

---

## 21. Conflict Resolution

### 21.1 Last-Write-Wins (LWW)

The simplest strategy: the most recent modification (by timestamp or version) overwrites older versions.

**Implementation:**

```sql
-- Server-side: accept the newer version
INSERT INTO tasks (id, title, status, updated_at, version)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    status = EXCLUDED.status,
    updated_at = EXCLUDED.updated_at,
    version = EXCLUDED.version
WHERE EXCLUDED.updated_at > tasks.updated_at;
```

**When to use:** Low-conflict domains (analytics, logging, single-user-per-record apps), settings/preferences, any case where the latest value is "correct enough."

**When NOT to use:** Collaborative editing, inventory management, financial records, or anywhere losing a concurrent edit is unacceptable.

**Pitfalls:**
- Clock skew between devices can cause the "wrong" write to win
- Silent data loss -- the user whose write is overwritten gets no notification
- Use HLC timestamps instead of wall-clock time to mitigate ordering issues

### 21.2 Server-Wins vs Client-Wins Policies

**Server-wins:** The server's current value always takes precedence. Client changes are silently discarded on conflict.

```python
# Server-wins: ignore client version if server is newer
if server_record.version >= client_record.version:
    return server_record  # client change discarded
else:
    apply(client_record)
```

**Client-wins:** The client's value always overwrites the server. Equivalent to LWW where client timestamp always "wins."

```python
# Client-wins: always accept client change
apply(client_record)
```

**When to use:**
- Server-wins: settings pushed from admin, read-only sync (server is source of truth)
- Client-wins: draft documents, personal notes, any data "owned" by one user

**Turso's conflict strategies demonstrate the spectrum:**
- `FAIL_ON_CONFLICT` -- reject sync, require explicit handling
- `DISCARD_LOCAL` -- server-wins
- `REBASE_LOCAL` -- replay local changes on top of server state (like git rebase)
- `MANUAL_RESOLUTION` -- callback with both versions for custom logic

### 21.3 Field-Level Merge

Instead of replacing entire rows, merge individual columns. If Device A changes `title` and Device B changes `status`, both changes are preserved.

**Implementation:**

```python
def field_level_merge(client_record, server_record, base_record):
    """Merge at column level using three-way comparison."""
    merged = {}
    for field in all_fields:
        client_changed = client_record[field] != base_record[field]
        server_changed = server_record[field] != base_record[field]
        
        if client_changed and not server_changed:
            merged[field] = client_record[field]    # client wins this field
        elif server_changed and not client_changed:
            merged[field] = server_record[field]    # server wins this field
        elif client_changed and server_changed:
            if client_record[field] == server_record[field]:
                merged[field] = client_record[field]  # both agree
            else:
                # True conflict on this field -- apply policy
                merged[field] = resolve_field_conflict(
                    field, client_record, server_record
                )
        else:
            merged[field] = base_record[field]      # neither changed
    return merged
```

**cr-sqlite uses per-column CRDTs for this:** Each column is independently tracked with its own version, so conflicting edits to different columns on the same row merge automatically. Only same-column, same-row conflicts require LWW fallback.

**When to use:** Any application where concurrent users typically edit different fields of the same record (task trackers, CRMs, project management).

**Pitfalls:**
- Requires storing the "base" version (the last-synced state) to do three-way comparison
- Field-level merge can produce semantically invalid combinations (e.g., changing `quantity` and `unit_price` independently can produce wrong `total`)
- Consider which fields should merge independently vs which should be treated as an atomic group

### 21.4 Operational Transformation (OT)

OT transforms concurrent operations against each other so both can be applied in any order and converge to the same result. Used primarily for text and sequence editing.

**How it works:**
1. User A inserts "X" at position 5
2. User B inserts "Y" at position 3
3. Server receives both operations
4. Server transforms A's operation: since B inserted before position 5, A's position shifts to 6
5. Both clients apply the transformed operations, converging to the same document

**When to use:** Collaborative text editing (Google Docs uses OT), sequential data where position matters.

**When NOT to use:** Simple key-value record sync, CRUD apps, scenarios without a central server (OT requires a server for ordering).

**Trade-offs vs CRDTs:**
- OT is simpler for text editing with a central server
- CRDTs work peer-to-peer without a central server
- OT requires all operations to pass through the server
- CRDTs have higher metadata overhead but work offline indefinitely

**Sources:**
- [OT vs CRDT Comparison (thom.ee)](https://thom.ee/blog/crdt-vs-operational-transformation/)
- [Real-Time Collaboration OT vs CRDT (TinyMCE)](https://www.tiny.cloud/blog/real-time-collaboration-ot-vs-crdt/)
- [Why Fiberplane Uses OT (Fiberplane)](https://fiberplane.com/blog/why-we-at-fiberplane-use-operational-transformation-instead-of-crdt/)

### 21.5 CRDTs (Conflict-Free Replicated Data Types)

CRDTs are data structures designed to automatically converge across replicas without coordination. If no more updates are made, all replicas reach the same state -- guaranteed by mathematical properties.

**CRDT types relevant to SQLite sync:**

| Type | Behavior | Use Case |
|------|----------|----------|
| **LWW-Register** | Last write wins per field, using timestamp | Individual record fields |
| **G-Counter** | Grow-only counter, each replica tracks its own count | Page views, like counts |
| **PN-Counter** | Positive-negative counter (two G-Counters) | Inventory, resource pools |
| **G-Set** | Grow-only set (add only, no remove) | Event logs, tags |
| **OR-Set** | Observed-Remove set (add and remove, add-wins) | Shopping carts, selections |
| **LWW-Element-Set** | Add/remove with timestamps | Feature flags, preferences |
| **MV-Register** | Multi-value register (preserves all concurrent writes) | Conflict-aware fields |
| **RGA** | Replicated Growable Array | Collaborative text, lists |

**cr-sqlite CRDT usage:**

```sql
-- Load the extension
.load crsqlite

-- Create a normal table
CREATE TABLE tasks (
    id TEXT PRIMARY KEY NOT NULL,
    title TEXT,
    status TEXT
);

-- Convert to a conflict-free replicated relation (CRR)
SELECT crsql_as_crr('tasks');

-- Normal INSERT/UPDATE/DELETE operations work as usual
INSERT INTO tasks (id, title, status) VALUES ('task-1', 'Buy groceries', 'pending');
UPDATE tasks SET status = 'done' WHERE id = 'task-1';

-- Export changes since version X for sync
SELECT "table", "pk", "cid", "val", "col_version", "db_version",
       "site_id", "cl", "seq"
FROM crsql_changes
WHERE db_version > ?;

-- Import changes from another device
INSERT INTO crsql_changes
    ("table", "pk", "cid", "val", "col_version", "db_version",
     "site_id", "cl", "seq")
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);

-- Clean up before closing
SELECT crsql_finalize();
```

**Performance characteristics of cr-sqlite:**
- Inserts into CRR tables: approximately 2.5x slower than regular SQLite
- Reads: identical speed to standard SQLite
- Space overhead: additional metadata for version tracking per column

**When to use CRDTs:** Peer-to-peer sync, multi-device apps with extended offline periods, collaborative editing, any scenario where a central server cannot always be reached.

**When NOT to use CRDTs:** Simple client-server sync where the server is always authoritative, apps where business logic validation must happen before accepting writes.

**Sources:**
- [cr-sqlite (GitHub)](https://github.com/vlcn-io/cr-sqlite)
- [CRDT Dictionary (Ian Duncan)](https://www.iankduncan.com/engineering/2025-11-27-crdt-dictionary/)
- [CRDT Implementations (crdt.tech)](https://crdt.tech/implementations)
- [Conflict-Free Replicated Data Types (Wikipedia)](https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type)

### 21.6 Conflict Queues for Manual Resolution

When automated resolution is insufficient, queue conflicts for human review.

**Conflict queue table:**

```sql
CREATE TABLE sync_conflicts (
    id TEXT PRIMARY KEY NOT NULL,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    client_data TEXT NOT NULL,      -- JSON of client version
    server_data TEXT NOT NULL,      -- JSON of server version
    base_data TEXT,                 -- JSON of last-synced version (for 3-way merge)
    conflict_type TEXT NOT NULL,    -- 'update_update', 'update_delete', 'delete_update'
    detected_at TEXT NOT NULL,
    resolved_at TEXT,
    resolution TEXT,                -- 'client', 'server', 'merged', 'discarded'
    resolved_data TEXT              -- JSON of final version if merged
);

CREATE INDEX idx_conflicts_unresolved
ON sync_conflicts(resolved_at) WHERE resolved_at IS NULL;
```

**Conflict detection during sync:**

```python
def sync_record(client_record, server_record):
    if server_record.version == client_record.base_version:
        # No conflict -- server hasn't changed since client last synced
        apply_to_server(client_record)
    else:
        # Conflict -- both changed since last sync
        conflict = {
            "table_name": "tasks",
            "record_id": client_record.id,
            "client_data": json.dumps(client_record),
            "server_data": json.dumps(server_record),
            "conflict_type": "update_update",
            "detected_at": now_utc()
        }
        insert_conflict(conflict)
        # Optionally: apply server version as interim, flag for review
```

**When to use:** Medical records, legal documents, financial transactions, any domain where silent data loss is unacceptable and a human must choose the correct resolution.

---
---
## 22. Sync Protocols and Patterns

### 22.1 Full Sync vs Incremental/Delta Sync

**Full sync:** Transfer the entire dataset on every sync. Simple but expensive.

```sql
-- Full sync: client sends everything
SELECT * FROM tasks;

-- Server replaces all client data
DELETE FROM tasks;
INSERT INTO tasks SELECT * FROM incoming_data;
```

**Incremental (delta) sync:** Transfer only records that changed since the last sync.

```sql
-- Client tracks last successful sync timestamp
-- or last sync version number
SELECT * FROM tasks
WHERE updated_at > ?   -- last_sync_timestamp
ORDER BY updated_at ASC;
```

**Delta sync with version numbers (more reliable than timestamps):**

```sql
-- Server maintains a global sync version counter
-- Each change increments it
-- Client stores the last version it received

-- Client pull: "give me everything after version 42"
SELECT * FROM tasks WHERE sync_version > 42 ORDER BY sync_version ASC;

-- Client push: send changes with their local version
-- Server assigns sequential sync_version on acceptance
```

**Best practice:** Always use delta sync in production. Full sync only for initial bootstrap or recovery after corruption.

### 22.2 Change Tracking Approaches

**Approach 1: Flag columns on each table**

```sql
-- updated_at + last_synced_at comparison
SELECT * FROM tasks
WHERE last_synced_at IS NULL OR updated_at > last_synced_at;
```

Pros: Simple. Cons: Requires adding columns to every synced table.

**Approach 2: Change log table with triggers**

```sql
CREATE TABLE change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    operation TEXT NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
    changed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    synced INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_changelog_unsynced ON change_log(synced, changed_at);

-- INSERT trigger
CREATE TRIGGER tasks_after_insert
AFTER INSERT ON tasks
BEGIN
    INSERT INTO change_log (table_name, record_id, operation)
    VALUES ('tasks', NEW.id, 'INSERT');
END;

-- UPDATE trigger
CREATE TRIGGER tasks_after_update
AFTER UPDATE ON tasks
BEGIN
    INSERT INTO change_log (table_name, record_id, operation)
    VALUES ('tasks', NEW.id, 'UPDATE');
END;

-- DELETE trigger
CREATE TRIGGER tasks_after_delete
AFTER DELETE ON tasks
BEGIN
    INSERT INTO change_log (table_name, record_id, operation)
    VALUES ('tasks', OLD.id, 'DELETE');
END;
```

Pros: Centralized change tracking, captures operation type. Cons: Table grows continuously, needs periodic purging.

**Approach 3: SQLite Session Extension**

The SQLite Session Extension is a built-in mechanism for recording changes to rowid tables and packaging them as binary changesets.

```c
// Create a session monitoring all tables
sqlite3_session *pSession;
sqlite3session_create(db, "main", &pSession);
sqlite3session_attach(pSession, NULL);  // NULL = all tables

// ... application makes changes ...

// Generate a binary changeset
void *pChangeset;
int nChangeset;
sqlite3session_changeset(pSession, &nChangeset, &pChangeset);

// Apply changeset to another database
sqlite3changeset_apply(db2, nChangeset, pChangeset, NULL, conflict_handler, NULL);

// Clean up
sqlite3session_delete(pSession);
```

Changeset contents per operation:
- **INSERT:** Values for all columns of the new row
- **DELETE:** Primary key + original values for all columns
- **UPDATE:** Primary key + original values + new values for changed columns

Changeset vs patchset:
- **Changeset:** Full old + new values; enables complete conflict detection
- **Patchset:** Compact format; DELETE carries only PK, UPDATE carries only new values; limited conflict detection

Build requirement: compile SQLite with `-DSQLITE_ENABLE_SESSION -DSQLITE_ENABLE_PREUPDATE_HOOK`

**Sources:**
- [SQLite Session Extension (sqlite.org)](https://sqlite.org/sessionintro.html)
- [SQLiteChangesetSync (GitHub)](https://github.com/gerdemb/SQLiteChangesetSync)
- [sqlite3session changeset example (GitHub Gist)](https://gist.github.com/kroggen/8329210e5f52a0b8b60e9c7f98b059a7)

### 22.3 Push vs Pull vs Bidirectional Sync

**Pull sync (server to client):**
- Client periodically requests new data from server
- Server is source of truth
- Simple to implement; polling introduces latency
- Use for read-heavy apps (news, documentation, catalog data)

**Push sync (client to server):**
- Client sends local changes to server when connectivity returns
- Server validates and applies
- Use for write-heavy offline scenarios (field data collection, surveys)

**Bidirectional sync:**
- Both push and pull in a single sync cycle
- Most complex; requires conflict resolution
- Standard pattern for collaborative apps

**Recommended sync cycle for bidirectional:**

```
1. Push local changes to server
2. Server validates, resolves conflicts, returns results
3. Pull server changes (including changes from other devices)
4. Apply server changes to local database
5. Update last_synced_at / sync version
```

**Push-based optimization via "shoulder tap":**
Instead of polling, the server sends a lightweight notification (push notification, WebSocket message, SSE event) that new data is available. The client then pulls the actual data. This combines low latency with simple pull-based data transfer.

### 22.4 Batch Sync with Pagination

Never sync unbounded result sets. Paginate using the sync version or timestamp.

```sql
-- Server: paginated sync endpoint
-- Client requests: GET /sync?since_version=42&limit=100

SELECT id, title, status, updated_at, version, is_deleted, sync_version
FROM tasks
WHERE sync_version > :since_version
ORDER BY sync_version ASC
LIMIT :limit;

-- Response includes the max sync_version in the batch
-- Client uses that as since_version for the next page
```

**Batch size recommendations:**
- Start with 100-500 records per batch
- Adjust based on average record size and network conditions
- Mobile: smaller batches (50-100) for unreliable connections
- Desktop: larger batches (500-1000) for stable connections
- Never exceed the SQLite parameter limit (999 for older versions, 32766 for newer)

### 22.5 Idempotent Operations for Retry Safety

Network failures during sync mean the same batch may be sent multiple times. Every sync operation must be safe to replay.

**Making operations idempotent:**

```sql
-- UPSERT pattern: safe to replay
INSERT INTO tasks (id, title, status, updated_at, version)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    status = EXCLUDED.status,
    updated_at = EXCLUDED.updated_at,
    version = EXCLUDED.version
WHERE EXCLUDED.version > tasks.version;
```

```sql
-- Soft delete: safe to replay
UPDATE tasks SET is_deleted = 1, updated_at = ?
WHERE id = ? AND is_deleted = 0;
-- If already deleted, this is a no-op (0 rows affected) -- safe
```

**Idempotency keys in the outbox:**

```sql
CREATE TABLE outbox (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    payload TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,  -- critical
    status TEXT NOT NULL DEFAULT 'pending',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);

-- INSERT OR IGNORE prevents duplicate entries on retry
INSERT OR IGNORE INTO outbox (id, type, payload, idempotency_key, created_at)
VALUES (?, ?, ?, ?, ?);
```

**Server-side deduplication:**

The server must also track processed idempotency keys and return success (not error) for duplicates:

```python
def process_sync_batch(changes):
    for change in changes:
        if already_processed(change.idempotency_key):
            continue  # idempotent: return success, don't reapply
        apply_change(change)
        mark_processed(change.idempotency_key)
```

### 22.6 Queue-Based Sync with Outbox Pattern

The outbox pattern ensures that local data writes and sync queue entries are always consistent -- either both happen or neither does.

**Outbox table schema:**

```sql
CREATE TABLE sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,         -- 'INSERT', 'UPDATE', 'DELETE'
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    payload TEXT NOT NULL,           -- JSON of the record
    idempotency_key TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    synced INTEGER NOT NULL DEFAULT 0,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    next_attempt_at INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_sync_unsynced ON sync_queue(synced, next_attempt_at);
```

**Transactional dual-write (critical pattern):**

```python
# BOTH the data write and queue entry in ONE transaction
db.execute("BEGIN TRANSACTION")

db.execute("""
    INSERT INTO tasks (id, title, status, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?)
""", [task_id, title, status, now, now])

db.execute("""
    INSERT INTO sync_queue (operation, table_name, record_id, payload, idempotency_key)
    VALUES ('INSERT', 'tasks', ?, ?, ?)
""", [task_id, json.dumps(task_data), f"insert:tasks:{task_id}"])

db.execute("COMMIT")
# If it's on screen, it's in the outbox.
```

**Sync worker (processes queue on reconnect):**

```python
def process_sync_queue():
    rows = db.execute("""
        SELECT id, operation, table_name, record_id, payload, attempt_count
        FROM sync_queue
        WHERE synced = 0 AND next_attempt_at <= ?
        ORDER BY id ASC
        LIMIT 50
    """, [now_ms()]).fetchall()
    
    for row in rows:
        try:
            response = send_to_server(row)
            if response.status_code in (200, 201, 204):
                db.execute("UPDATE sync_queue SET synced = 1 WHERE id = ?", [row.id])
            elif response.status_code == 409:  # conflict
                handle_conflict(row, response.json())
        except NetworkError:
            # Exponential backoff, capped at 15 minutes
            next_attempt = now_ms() + min(
                15 * 60_000,
                30_000 * (row.attempt_count + 1)
            )
            db.execute("""
                UPDATE sync_queue
                SET attempt_count = attempt_count + 1,
                    next_attempt_at = ?
                WHERE id = ?
            """, [next_attempt, row.id])
```

**Inbound sync (applying server changes locally):**

```python
def apply_server_changes(changes):
    db.execute("BEGIN TRANSACTION")
    for change in changes:
        if change["operation"] == "INSERT":
            db.execute("""
                INSERT OR REPLACE INTO tasks (id, title, status, updated_at, version)
                VALUES (?, ?, ?, ?, ?)
            """, [change["id"], change["title"], change["status"],
                  change["updated_at"], change["version"]])
        elif change["operation"] == "DELETE":
            db.execute("""
                UPDATE tasks SET is_deleted = 1, updated_at = ?
                WHERE id = ?
            """, [change["updated_at"], change["id"]])
    db.execute("COMMIT")
```

**Sources:**
- [Outbox Pattern (Milan Jovanovic)](https://www.milanjovanovic.tech/blog/implementing-the-outbox-pattern)
- [Transactional Outbox Pattern (microservices.io)](https://microservices.io/patterns/data/transactional-outbox.html)
- [React Native Offline Sync with SQLite Queue (DEV)](https://dev.to/sathish_daggula/react-native-offline-sync-with-sqlite-queue-4975)
- [Offline-First Apps with SQLite Sync Queues (SQLite Forum)](https://www.sqliteforum.com/p/building-offline-first-applications-4f4)

---

## 23. Offline-First Architecture

### 23.1 Write-Ahead Log for Offline Operations

SQLite's WAL mode is foundational for offline-first apps.

**Enable WAL mode:**

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;  -- safe for app crashes, not power loss
```

**Why WAL matters for sync:**
- Readers never block writers and writers never block readers
- Write transactions are fast (sequential log append, no fsync per commit in NORMAL mode)
- Background sync reads can proceed while the user writes data
- WAL can be replicated (Litestream, Turso use this)

**Connection strategy for sync:**
- One writer connection (serialized writes via application-level queue)
- Multiple reader connections (parallel reads for UI and sync)
- Never share a single connection between UI thread and sync thread

### 23.2 Operation Queue Pattern

Queue every mutation as a discrete operation. Replay the queue when connectivity returns.

**Queue table:**

```sql
CREATE TABLE outbox (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,               -- 'create_task', 'update_task', 'delete_task'
    payload TEXT NOT NULL,            -- JSON with all data needed to replay
    idempotency_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'sending', 'done', 'failed'
    attempt_count INTEGER NOT NULL DEFAULT 0,
    next_attempt_at INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);

CREATE INDEX idx_outbox_pending
ON outbox(status, next_attempt_at)
WHERE status = 'pending';
```

**Critical rule:** The UI write and the outbox entry must be in the same transaction. If it is on screen, it is in the outbox.

**Event-sourcing variant:** Instead of storing record snapshots, store operations:

```json
{"type": "set_logged", "set_id": "abc", "reps": 10, "weight": 135}
{"type": "set_deleted", "set_id": "abc"}
{"type": "workout_renamed", "workout_id": "xyz", "name": "Leg Day"}
```

The server replays these events to reconstruct state. This makes sync equivalent to event replay and naturally supports undo/redo.

### 23.3 Optimistic UI Updates

The UI always reads from the local SQLite database, never from the network. Changes appear instantly.

**Pattern:**

```
User Action
    |
    v
Write to local SQLite + Enqueue to outbox (one transaction)
    |
    v
UI reads from SQLite (instant update)
    |
    v (background, asynchronous)
Sync worker sends outbox to server
    |
    v
Server confirms or rejects
    |
    v
If rejected: roll back local change, notify user
If confirmed: mark outbox entry as done
```

**Rollback on server rejection:**

```python
def handle_server_rejection(outbox_entry, server_response):
    db.execute("BEGIN TRANSACTION")
    # Revert the local change
    if outbox_entry.type == 'create_task':
        db.execute("DELETE FROM tasks WHERE id = ?", [outbox_entry.record_id])
    elif outbox_entry.type == 'update_task':
        # Restore from server's version
        apply_server_version(server_response.current_record)
    # Remove from outbox
    db.execute("UPDATE outbox SET status = 'failed' WHERE id = ?", [outbox_entry.id])
    db.execute("COMMIT")
    notify_user("Your change could not be saved: " + server_response.reason)
```

### 23.4 Schema Migrations When Device Is Offline

Devices may be offline when a new app version with schema changes is released.

**Migration strategy using user_version pragma:**

```python
def migrate_database(db):
    db.execute("PRAGMA user_version")
    current_version = db.fetchone()[0]
    
    if current_version < 1:
        db.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium'")
        db.execute("CREATE INDEX idx_tasks_priority ON tasks(priority)")
        db.execute("PRAGMA user_version = 1")
    
    if current_version < 2:
        db.execute("""
            CREATE TABLE task_tags (
                task_id TEXT NOT NULL REFERENCES tasks(id),
                tag TEXT NOT NULL,
                PRIMARY KEY (task_id, tag)
            )
        """)
        db.execute("PRAGMA user_version = 2")
    
    if current_version < 3:
        # Complex migration: rename column (SQLite < 3.25 workaround)
        db.execute("BEGIN TRANSACTION")
        db.execute("ALTER TABLE tasks RENAME TO tasks_old")
        db.execute("""
            CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,  -- renamed from 'content'
                -- ... all other columns
            )
        """)
        db.execute("""
            INSERT INTO tasks (id, title, description, ...)
            SELECT id, title, content, ... FROM tasks_old
        """)
        db.execute("DROP TABLE tasks_old")
        db.execute("COMMIT")
        db.execute("PRAGMA user_version = 3")
```

**Migration tracking table (alternative to pragma):**

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
```

**Rules for sync-compatible migrations:**
1. Only add columns -- never remove or rename without a migration path
2. New columns must have DEFAULT values (CRDTs require this)
3. Migrations must be idempotent (safe to run twice)
4. Wrap each migration in a transaction
5. Always back up before migrating
6. Test migrations against databases at every previous version

**Sources:**
- [SQLite Versioning and Migration Strategies (SQLite Forum)](https://www.sqliteforum.com/p/sqlite-versioning-and-migration-strategies)
- [Android SQLite Database Migration (Medium)](https://medium.com/mobile-app-development-publication/android-sqlite-database-migration-b9ad47811d34)

### 23.5 Data Expiry and Cache Invalidation

Local SQLite databases grow unbounded without maintenance.

**Pruning synced data:**

```sql
-- Remove successfully synced outbox entries older than 30 days
DELETE FROM sync_queue
WHERE synced = 1
  AND created_at < strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-30 days');

-- Remove old change log entries
DELETE FROM change_log
WHERE synced = 1
  AND changed_at < strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-30 days');

-- Purge tombstones older than 90 days (confirmed synced)
DELETE FROM tasks WHERE is_deleted = 1
  AND updated_at < strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-90 days')
  AND last_synced_at IS NOT NULL;
```

**VACUUM after pruning:**

```sql
-- Reclaim disk space (locks database, copies and rebuilds)
VACUUM;

-- Check space usage before deciding to vacuum
SELECT page_count * page_size AS total_size,
       freelist_count * page_size AS free_space
FROM pragma_page_count(), pragma_page_size(), pragma_freelist_count();
```

**Incremental vacuum (less disruptive alternative):**

```sql
PRAGMA auto_vacuum = INCREMENTAL;
PRAGMA incremental_vacuum(100);  -- free up to 100 pages
```

**Cache invalidation strategy:**
- Track `last_full_sync` timestamp
- If `last_full_sync` is older than threshold (e.g., 7 days), do a full sync instead of delta
- If server sends a "schema changed" signal, drop and rebuild local tables
- Monitor storage quota (especially important in browsers):

```javascript
const estimate = await navigator.storage.estimate();
const percentUsed = (estimate.usage / estimate.quota) * 100;
if (percentUsed > 80) {
    // Trigger aggressive pruning
    await pruneOldSyncData();
}
```

---

## 4. Clock Systems and Ordering

Sync systems need a way to determine the order of events across distributed devices. The choice of clock system affects conflict resolution accuracy, storage overhead, and implementation complexity.

### 4.1 Physical Clocks

Wall-clock timestamps (`datetime('now')`, `System.currentTimeMillis()`, `Date.now()`). Simple but vulnerable to clock skew between devices, NTP corrections, and manual time changes.

**When acceptable:** Single-user-per-record apps, systems where the server assigns all timestamps, or when ordering accuracy within a few seconds is sufficient.

**When problematic:** Multi-device concurrent edits where ordering correctness matters. Two devices with 30-second clock drift will disagree on which write was "last."

### 4.2 Lamport Timestamps

A simple incrementing counter. Each event gets the next value; when a message arrives with a higher counter, the local counter jumps forward.

**Property:** Guarantees `e happened before f => L(e) < L(f)`, but the converse is NOT true — two events with `L(e) < L(f)` may be concurrent. Cannot distinguish "happened-before" from "concurrent."

**When to use:** Systems that only need causal ordering guarantees. Low overhead (single integer).

### 4.3 Vector Clocks

Array of counters, one per device/replica. Can distinguish "happened-before" from "concurrent" events — the key advantage over Lamport timestamps.

**Limitation:** Space grows O(n) where n = number of devices. Impractical for consumer apps with many devices. Well-suited for systems with a small, known set of replicas (e.g., 3-5 database nodes).

### 4.4 Hybrid Logical Clocks (HLC)

Combine physical wall-clock time with a logical counter in a single 64-bit value:

```
HLC timestamp = [48-bit physical time] + [16-bit logical counter]
```

**Properties:**
- Remain close to wall-clock time (useful for debugging and human-readable ordering)
- Guarantee causal ordering (strictly monotonic per-node)
- Self-stabilizing against NTP corrections
- Single 64-bit value — no per-device array growth

**Recommended for most sync systems.** They provide the ordering guarantees of logical clocks while remaining close to physical time.

**Sources:**
- [Hybrid Logical Clocks (Sergei Turukin)](https://sergeiturukin.com/2017/06/26/hybrid-logical-clocks.html)
- [Evolving Clock Sync in Distributed Databases (YugabyteDB)](https://www.yugabyte.com/blog/evolving-clock-sync-for-distributed-databases/)

### 4.5 Server-Assigned Monotonic Versions

Instead of relying on client clocks, the server assigns a strictly increasing version number to every accepted change using a database sequence.

```sql
-- PostgreSQL: monotonic sync version
CREATE SEQUENCE sync_version_seq;

-- On every INSERT or UPDATE accepted during sync:
UPDATE tasks SET sync_version = nextval('sync_version_seq') WHERE id = ?;
```

**Properties:**
- Zero clock-skew issues — the server is the sole source of ordering
- Clients request "everything after version N" for efficient delta pulls
- Simple to implement and reason about
- Requires server connectivity to assign versions (not pure peer-to-peer)

**When to use:** Client-server architectures where all writes are validated by the server. This is the most common pattern in production sync systems (Linear, Figma, and many mobile apps use variants of this).

---

## 5. Sync Engine Design

Principles for designing the client-side sync engine that orchestrates local-remote synchronization.

### 5.1 Architecture Layers

A well-structured sync engine separates concerns into distinct layers:

```
┌──────────────────────────────────┐
│           Application            │
│  (reads from local DB, writes    │
│   through sync-aware mutations)  │
├──────────────────────────────────┤
│         Sync Orchestrator        │
│  (coordinates push/pull cycles,  │
│   manages sync state/versions)   │
├──────────────────────────────────┤
│       Content Type Handlers      │
│  (per-entity sync logic: what    │
│   to collect, how to upsert)     │
├──────────────────────────────────┤
│          Sync Transport          │
│  (HTTP client, WebSocket, or     │
│   platform-specific IPC)         │
├──────────────────────────────────┤
│         Local Database           │
│  (SQLite, Room, Core Data, etc.) │
└──────────────────────────────────┘
```

### 5.2 Entity-Agnostic Infrastructure

Design the sync engine so new entity types can be added with minimal boilerplate:

```
interface Syncable<T> {
    collectDirty(): List<T>           // gather unsynced local records
    buildPayload(items: List<T>)      // serialize for sync request
    applyResponse(items: List<T>)     // upsert server response locally
    markSynced(items: List<T>)        // clear dirty flags
}
```

Each content type (tasks, projects, events, etc.) implements this interface. The sync orchestrator iterates over registered content types without knowing their details.

**Benefits:**
- Adding a new synced entity is a single interface implementation
- Sync logic is tested once in the orchestrator, not per entity
- Content types can have custom conflict handling while sharing transport and scheduling

### 5.3 The Sync Cycle

A standard bidirectional sync cycle in a single round trip:

```
1. Collect    — Query local records where isDirty = true
2. Package    — Build request: { lastSyncVersion, dirtyRecords[] }
3. Send       — POST /api/sync (single endpoint, all entity types)
4. Receive    — Server returns: { currentSyncVersion, changedRecords[] }
5. Apply      — Upsert server records locally, clear dirty flags
6. Checkpoint — Store currentSyncVersion for next sync
```

**Combined push/pull:** Sending dirty records and requesting changes in a single HTTP request halves the round trips versus separate push and pull calls. This matters significantly on mobile networks with high latency.

### 5.4 Dirty Tracking Strategies

**Flag column (`isDirty`):**
- Add `is_dirty INTEGER NOT NULL DEFAULT 0` to each synced table
- Set to 1 on every local INSERT/UPDATE
- Clear to 0 after successful sync
- Simple, low overhead, works everywhere

**Change log table:**
- Central table records (table_name, record_id, operation, timestamp)
- Triggers on each synced table populate the log
- More information (operation type, ordering) but more maintenance

**Edit operations table:**
- Records field-level edits with timestamps and device IDs
- Enables field-level merge on the server
- Highest fidelity but most complex

**Recommendation:** Start with `isDirty` flag columns. Upgrade to a change log or edit operations only if you need operation-type awareness or field-level merge.

### 5.5 Sync Scheduling

**Periodic sync:** Run every N seconds (e.g., 30s) when the app is active. Simple, predictable, battery-friendly.

**Event-driven sync:** Trigger immediately on user action (save, delete) plus periodic as a safety net. More responsive but can create bursts of traffic.

**Background daemon:** Platform-specific background process handles sync when the app is closed:
- **macOS/iOS:** XPC service or Background App Refresh
- **Android:** WorkManager with periodic constraints
- **Windows:** Background service or scheduled task
- **Web:** Service Worker with periodic sync API

**Connectivity-aware:** Monitor network state. Queue sync attempts when offline, trigger immediate sync on reconnection.

### 5.6 Error Handling and Retry

**Exponential backoff with jitter:**

```
delay = min(MAX_DELAY, BASE_DELAY * 2^attempt) + random(0, JITTER)
```

Typical values: BASE_DELAY = 1s, MAX_DELAY = 15min, JITTER = 0-1s.

**Retry categories:**
- **Transient errors** (network timeout, 503): retry with backoff
- **Client errors** (400, 401, 403): do not retry, surface to user
- **Conflict errors** (409): handle via conflict resolution strategy, do not retry blindly
- **Server errors** (500): retry with longer backoff

**Circuit breaker:** After N consecutive failures, stop attempting sync and enter a degraded mode. Resume on explicit user action or after a cooldown period.

### 5.7 Snapshot Rebuilding

After applying sync changes, some entities need derived state rebuilt:

```
1. Receive server changes for entity X
2. Upsert raw records
3. Rebuild computed views/snapshots that depend on X
4. Notify UI of changes
```

This is especially important for entities with edit history — the current state may be a function of applying all edits in order, not just the latest record.

---

*Research compiled from production sync implementations, academic distributed systems literature, and practitioner sources. Last updated April 2026.*
