---

id: A899AEAE-D561-4FCD-ABD7-DF109FE2362C
title: "Sync Schema Design"
domain: agentic-cookbook://guidelines/implementing/data/sync-schema-design
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Schema design rules for databases that sync across devices: UUID primary keys, timestamp columns, soft deletes, dirty tracking, version columns, and sync metadata tables."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - sync
  - schema
  - offline-first
  - uuid
  - soft-delete
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
  - guidelines/data/conflict-resolution.md
  - guidelines/data/sync-protocol.md
references:
  - https://sqlite.org/datatype3.html
  - https://vlcn.io/docs/cr-sqlite
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - offline-support
  - schema-design
---

# Sync Schema Design

Every table that participates in sync requires specific structural choices that cannot be retrofitted easily. These rules apply to both the local SQLite schema and the corresponding server PostgreSQL schema.

## Primary Keys: Always UUID

MUST use UUID primary keys for all synced tables. Never use `INTEGER PRIMARY KEY AUTOINCREMENT` for synced tables — auto-incremented integers are generated locally by each device and will collide across devices when syncing.

Use **UUIDv7** (time-ordered) where possible. UUIDv7 embeds a timestamp prefix, preserving roughly-chronological insert ordering while guaranteeing global uniqueness. PostgreSQL 17+ supports `gen_random_uuid()` or `uuid_generate_v7()`.

```sql
-- SQLite: sync-ready table
CREATE TABLE tasks (
    id          TEXT    PRIMARY KEY NOT NULL,   -- UUIDv7, generated client-side
    title       TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'pending',
    created_at  TEXT    NOT NULL,               -- ISO-8601 UTC
    updated_at  TEXT    NOT NULL,               -- ISO-8601 UTC
    version     INTEGER NOT NULL DEFAULT 1,
    is_deleted  INTEGER NOT NULL DEFAULT 0,
    last_synced_at TEXT                         -- NULL until first sync
);

-- PostgreSQL: corresponding server table
CREATE TABLE tasks (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    title       TEXT        NOT NULL,
    status      TEXT        NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    version     INTEGER     NOT NULL DEFAULT 1,
    is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE,
    last_synced_at TIMESTAMPTZ
);
```

## Timestamp Columns

Every synced table MUST have three timestamp columns:

| Column | Purpose |
|--------|---------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| `created_at` | Record creation time (set once, never updated) |
| `updated_at` | Last modification time (updated on every change) |
| `last_synced_at` | Last successful server sync (NULL until first sync) |

Store all timestamps as **ISO-8601 UTC strings** in SQLite (`TEXT`), and as `TIMESTAMPTZ` in PostgreSQL. Never mix formats within a column.

Use a trigger to keep `updated_at` current automatically:

```sql
CREATE TRIGGER tasks_update_timestamp
AFTER UPDATE ON tasks
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE tasks SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE id = NEW.id;
END;
```

Detect unsynced records with:

```sql
SELECT * FROM tasks
WHERE last_synced_at IS NULL
   OR updated_at > last_synced_at;
```

## Version Columns for Optimistic Concurrency

MUST add a `version INTEGER NOT NULL DEFAULT 1` column to every synced table. The version column is the authoritative signal for conflict detection.

On update: increment the version. On sync, the server applies the write only if the client's base version matches the server's current version. A mismatch signals a conflict.

```sql
UPDATE tasks
SET title = ?, version = version + 1, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
WHERE id = ? AND version = ?;
-- Check sqlite3_changes() == 1. If 0, conflict occurred.
```

## Soft Deletes (Tombstones)

MUST NOT hard-delete records from synced tables. Hard deletes cannot be propagated — there is nothing left to sync.

Use `is_deleted INTEGER NOT NULL DEFAULT 0` (SQLite) / `is_deleted BOOLEAN NOT NULL DEFAULT FALSE` (PostgreSQL). All normal queries filter on `is_deleted = 0`; sync queries include deleted records.

```sql
-- Deletion
UPDATE tasks SET is_deleted = 1, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
WHERE id = ?;

-- Normal query
SELECT * FROM tasks WHERE is_deleted = 0;

-- Index to keep filtering fast
CREATE INDEX idx_tasks_is_deleted ON tasks(is_deleted);
```

For high-volume tables, a separate tombstone table keeps the live table lean:

```sql
CREATE TABLE tasks_tombstones (
    id          TEXT NOT NULL PRIMARY KEY,
    deleted_at  TEXT NOT NULL,
    synced      INTEGER NOT NULL DEFAULT 0
);

-- Purge tombstones confirmed synced to all devices
DELETE FROM tasks_tombstones
WHERE synced = 1
  AND deleted_at < strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-90 days');
```

## Dirty Tracking

SHOULD add `is_dirty INTEGER NOT NULL DEFAULT 0` to each synced table (or a central change-log table fed by triggers). Set to `1` on every local insert or update; clear to `0` after the sync worker confirms the server accepted the change.

For apps needing operation-type awareness (INSERT vs UPDATE vs DELETE), use a change-log table with triggers instead of the flag column.

## Sync Metadata Tables

Add a `sync_state` table (or equivalent) to store per-device checkpoint information:

```sql
CREATE TABLE sync_state (
    key     TEXT PRIMARY KEY NOT NULL,  -- e.g. 'last_sync_version', 'device_id'
    value   TEXT NOT NULL
);
```

Store the last server-assigned sync version here after each successful sync. Use it as the `since_version` parameter on the next pull.

## Type Compatibility Between SQLite and PostgreSQL

Design columns so the same logical value maps cleanly across both databases:

| Type | SQLite DDL | PostgreSQL DDL |
|------|-----------|----------------|
| UUID | `TEXT` | `UUID` |
| Boolean | `INTEGER` (0/1) | `BOOLEAN` |
| Timestamp | `TEXT` (ISO-8601 UTC) | `TIMESTAMPTZ` |
| JSON | `TEXT` | `JSONB` |

Always use UTC. Convert to local time only at the display layer.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
