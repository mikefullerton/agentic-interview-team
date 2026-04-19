---

id: 0D3E2D97-22D4-4781-A6C4-FA297B38030F
title: "Offline-First Architecture"
domain: agentic-cookbook://guidelines/implementing/data/offline-first-architecture
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Design rules for offline-first apps: WAL as the foundation, operation queues, optimistic UI updates, rollback on rejection, offline schema migrations, data expiry, and connectivity-aware sync scheduling."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - sync
  - offline-first
  - wal
  - optimistic-ui
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
  - guidelines/data/sync-schema-design.md
  - guidelines/data/sync-protocol.md
references:
  - https://sqlite.org/wal.html
  - https://www.powersync.com/blog/sqlite-optimizations-for-ultra-high-performance
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - offline-support
  - database-operations
---

# Offline-First Architecture

An offline-first app works fully without network connectivity. The local database is the primary data store; the server is a synchronization target, not a dependency. Network availability is an optimization, not a requirement.

## WAL Mode as the Foundation

MUST enable WAL mode on every SQLite database that participates in sync:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;  -- safe for app crashes; use FULL only for power-loss safety
PRAGMA busy_timeout = 5000;   -- wait up to 5s instead of returning SQLITE_BUSY immediately
```

WAL mode enables concurrent readers and writers: readers never block writers, writers never block readers. This is essential for offline-first apps where the sync worker writes in the background while the UI reads. With the default rollback journal, a background write locks the entire database and freezes the UI.

SHOULD use one writer connection (writes serialized via an application-level queue) and multiple reader connections. Never hold a write transaction open while waiting on network I/O.

## Operation Queue Pattern

Every user mutation MUST be written to both the data table and an outbox queue in a single atomic transaction. This guarantees that whatever is visible on screen is queued for sync.

```python
db.execute("BEGIN TRANSACTION")
db.execute(
    "INSERT INTO tasks (id, title, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
    [task_id, title, "pending", now, now]
)
db.execute(
    "INSERT INTO outbox (id, type, payload, idempotency_key, status, created_at) "
    "VALUES (?, 'create_task', ?, ?, 'pending', ?)",
    [queue_id, json.dumps(task_data), f"create_task:{task_id}", now]
)
db.execute("COMMIT")
```

An event-sourcing variant stores the operation rather than a snapshot:

```json
{"type": "task_created", "task_id": "abc", "title": "Buy groceries"}
{"type": "task_status_changed", "task_id": "abc", "status": "done"}
```

The server replays these events to reconstruct state. This approach naturally supports undo/redo and makes sync equivalent to event replay.

## Optimistic UI Updates

The UI MUST read exclusively from local SQLite, never from the network. Changes appear instantly after the local write — the user does not wait for the server.

```
User action
  → Write to local SQLite + enqueue to outbox (one transaction)
  → UI reads from SQLite (instant — no network round trip)
  → Background: sync worker sends outbox to server
      → If server confirms: mark outbox entry as done
      → If server rejects: roll back local change, notify user
```

This means every write the user sees is "optimistic" — it is applied locally before the server confirms it. Design the UI to handle the rare case where the server rejects a write.

## Rollback on Server Rejection

MUST implement rollback when the server rejects an optimistic write. Silently ignoring rejections causes local and server state to diverge permanently.

```python
def handle_rejection(outbox_entry, server_response):
    db.execute("BEGIN TRANSACTION")
    if outbox_entry.type == "create_task":
        db.execute("DELETE FROM tasks WHERE id = ?", [outbox_entry.record_id])
    elif outbox_entry.type == "update_task":
        # Restore the server's authoritative version
        apply_server_version(server_response.current_record)
    db.execute(
        "UPDATE outbox SET status = 'failed' WHERE id = ?",
        [outbox_entry.id]
    )
    db.execute("COMMIT")
    notify_user("Change could not be saved: " + server_response.reason)
```

## Schema Migrations While Offline

Devices may be offline when a new app version with schema changes ships. Migrations MUST run successfully regardless of network state.

Use `PRAGMA user_version` to track the applied schema version:

```python
def migrate(db):
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version < 1:
        db.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium'")
        db.execute("PRAGMA user_version = 1")
    if version < 2:
        db.execute("BEGIN TRANSACTION")
        # For complex changes: create new table, copy, drop old
        db.execute("COMMIT")
        db.execute("PRAGMA user_version = 2")
```

Rules for sync-compatible migrations:

1. MUST only add columns — never remove or rename without a migration path
2. New columns MUST have DEFAULT values (required by CRDTs and outbox replay)
3. Migrations MUST be idempotent (safe to run twice)
4. MUST wrap each migration step in a transaction
5. MUST test migrations against databases at every previous schema version

## Data Expiry and VACUUM

Local SQLite databases grow unbounded without maintenance. Sync metadata — outbox entries, change logs, tombstones — accumulates fastest.

Prune on a schedule (e.g., on app launch or after sync completes):

```sql
-- Purge completed outbox entries older than 7 days
DELETE FROM outbox
WHERE status = 'done'
  AND created_at < strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-7 days');

-- Purge synced change log entries older than 30 days
DELETE FROM change_log
WHERE synced = 1
  AND changed_at < strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-30 days');

-- Hard-delete confirmed tombstones older than 90 days
DELETE FROM tasks
WHERE is_deleted = 1
  AND last_synced_at IS NOT NULL
  AND updated_at < strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-90 days');
```

After significant deletions, reclaim disk space with incremental vacuum (less disruptive than full VACUUM):

```sql
-- Check space before deciding
SELECT page_count * page_size AS total_bytes,
       freelist_count * page_size AS free_bytes
FROM pragma_page_count(), pragma_page_size(), pragma_freelist_count();

-- Gradual reclamation (does not lock the database for long)
PRAGMA incremental_vacuum(500);  -- free up to 500 pages
```

SHOULD trigger a full sync (not delta) if `last_full_sync` is older than a threshold (e.g., 7 days), to catch any gaps from previous sync failures.

## Connectivity-Aware Scheduling

MUST monitor network reachability and adjust sync behavior accordingly:

- When offline: queue writes locally, do not attempt sync
- On reconnection: trigger an immediate sync cycle
- When online: run periodic background sync (e.g., every 30 seconds while the app is active)
- When backgrounded: use platform-specific background sync APIs (WorkManager on Android, Background App Refresh on iOS, Service Worker Periodic Sync on web)

Never retry sync in a tight loop on reconnection. Apply exponential backoff starting from the first failure, even after regaining connectivity, in case the server is under load.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
