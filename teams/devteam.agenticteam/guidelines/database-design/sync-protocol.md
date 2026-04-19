---

id: 3B88BB39-A15D-488F-A967-B7FA2DBA2BE7
title: "Sync Protocol"
domain: agentic-cookbook://guidelines/implementing/data/sync-protocol
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Rules for designing the sync protocol between client and server: push/pull direction, full vs incremental sync, change tracking, batching, idempotency, the outbox pattern, and retry with backoff."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - sync
  - protocol
  - outbox
  - idempotency
  - offline-first
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
  - guidelines/data/sync-schema-design.md
  - guidelines/data/sync-engine-design.md
references:
  - https://microservices.io/patterns/data/transactional-outbox.html
  - https://www.milanjovanovic.tech/blog/implementing-the-outbox-pattern
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - offline-support
  - networking
  - database-operations
---

# Sync Protocol

The sync protocol defines how local changes travel to the server and how server changes arrive on the client. The protocol must be correct under network failure — retries, partial delivery, and out-of-order arrival are the norm, not the exception.

## Sync Direction

**Pull-only:** Client polls the server for new data. The server is the source of truth. Use for read-heavy apps (catalogs, news feeds, configuration).

**Push-only:** Client sends local changes when connectivity returns. Use for write-heavy offline scenarios (field data collection, surveys).

**Bidirectional (standard pattern):** Push local changes and pull server changes in a single round trip:

```
1. Push  — send dirty local records to server
2. Server validates, resolves conflicts, returns results
3. Pull  — receive server changes (including other devices)
4. Apply — upsert server records locally, clear dirty flags
5. Checkpoint — store the server's current sync version
```

SHOULD combine push and pull into a single HTTP request. Separate push and pull calls double the round trips, which is costly on high-latency mobile networks.

**Shoulder-tap optimization:** Rather than polling, have the server send a lightweight notification (push notification, WebSocket message, or SSE event) that new data is available. The client then pulls the actual data. This achieves low latency without a persistent connection for data transfer.

## Full Sync vs Incremental (Delta) Sync

MUST use incremental sync in production. Full sync (transfer everything every time) is only acceptable for initial bootstrap or recovery after database corruption.

Incremental sync using a version number (preferred over timestamp-based):

```sql
-- Client pulls: "give me everything after version 42"
SELECT id, title, status, updated_at, version, is_deleted, sync_version
FROM tasks
WHERE sync_version > 42
ORDER BY sync_version ASC
LIMIT 100;
-- Response includes the max sync_version in the batch
-- Client stores that as the checkpoint for the next pull
```

Timestamp-based delta sync is simpler but vulnerable to clock skew. If using timestamps, use Hybrid Logical Clocks (HLC) rather than wall-clock time.

## Change Tracking

Choose one of three approaches based on complexity needs:

**Flag columns** — simplest. Add `is_dirty INTEGER NOT NULL DEFAULT 0` to each synced table. Set to `1` on every local write; clear to `0` after the server confirms the change.

**Change-log table with triggers** — more information. A central table records the entity, record ID, operation type (INSERT/UPDATE/DELETE), and timestamp. Triggers on each synced table populate it.

```sql
CREATE TABLE change_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name  TEXT NOT NULL,
    record_id   TEXT NOT NULL,
    operation   TEXT NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
    changed_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    synced      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_changelog_unsynced ON change_log(synced, changed_at);
```

**SQLite Session Extension** — binary changesets. Records exact pre- and post-values for every row change, packaged as a binary blob for transport. Requires compile-time flags. Best when replaying changes to another SQLite database with the same schema.

## Batch Sync with Pagination

MUST paginate sync results. Never request or deliver unbounded result sets.

Use the server-assigned sync version as the cursor — not an offset. Offset-based pagination skips records if new changes arrive during sync.

Recommended batch sizes:

| Context | Batch Size |
|---------|-----------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Mobile (unstable network) | 50–100 records |
| Desktop (stable network) | 500–1000 records |
| Initial bootstrap | 1000–5000 records |
| Background sync | 100–500 records |

## Idempotent Operations

Every sync operation MUST be safe to replay. Network failures mean the same batch may be delivered multiple times.

Use UPSERT with a version guard so replaying an older batch never downgrades a record:

```sql
INSERT INTO tasks (id, title, status, updated_at, version)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT (id) DO UPDATE SET
    title      = EXCLUDED.title,
    status     = EXCLUDED.status,
    updated_at = EXCLUDED.updated_at,
    version    = EXCLUDED.version
WHERE EXCLUDED.version > tasks.version;
```

Use **idempotency keys** in the outbox to prevent duplicate processing on the server:

```sql
CREATE TABLE sync_queue (
    id               TEXT PRIMARY KEY,
    idempotency_key  TEXT NOT NULL UNIQUE,   -- deterministic: "insert:tasks:<id>"
    operation        TEXT NOT NULL,
    table_name       TEXT NOT NULL,
    record_id        TEXT NOT NULL,
    payload          TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'pending',
    attempt_count    INTEGER NOT NULL DEFAULT 0,
    next_attempt_at  INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Prevent duplicates on retry
INSERT OR IGNORE INTO sync_queue (id, idempotency_key, operation, table_name, record_id, payload)
VALUES (?, ?, ?, ?, ?, ?);
```

The server MUST also deduplicate on idempotency key and return success (not an error) for already-processed requests.

## Outbox Pattern

MUST write to the local data table and the sync queue in a single transaction. This guarantees the outbox always reflects local state — there is no window where a change is visible on screen but not queued for sync.

```python
db.execute("BEGIN TRANSACTION")

db.execute(
    "INSERT INTO tasks (id, title, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
    [task_id, title, status, now, now]
)
db.execute(
    "INSERT INTO sync_queue (id, idempotency_key, operation, table_name, record_id, payload) "
    "VALUES (?, ?, 'INSERT', 'tasks', ?, ?)",
    [queue_id, f"insert:tasks:{task_id}", task_id, json.dumps(task_data)]
)

db.execute("COMMIT")
# If the task is on screen, it is in the outbox.
```

The sync worker processes the queue asynchronously, retrying failed entries with exponential backoff. Completed entries can be pruned after a retention window (e.g., 7 days for debugging).

## Retry with Exponential Backoff

MUST implement exponential backoff with jitter for failed sync attempts. Never retry in a tight loop.

```
delay = min(MAX_DELAY, BASE_DELAY * 2^attempt) + random(0, JITTER)
```

Typical values: `BASE_DELAY = 1s`, `MAX_DELAY = 15min`, `JITTER = 0–1s`.

Classify errors before retrying:

| Error Category | Action |
|---------------|--------|
| Transient (timeout, 503) | Retry with backoff |
| Client error (400, 401, 403) | Do not retry — surface to user |
| Conflict (409) | Apply conflict resolution strategy, do not retry blindly |
| Server error (500) | Retry with longer backoff |

After N consecutive failures, enter a circuit-breaker state: stop attempting sync and resume only after a cooldown period or explicit user action.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
