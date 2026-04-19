---

id: 0ECFED07-C7A7-4E76-9F3E-1C5EA0A5DCE8
title: "Primary key strategies"
domain: agentic-cookbook://guidelines/implementing/data/primary-keys
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Choosing between INTEGER PRIMARY KEY, AUTOINCREMENT, UUID, and WITHOUT ROWID — including sync compatibility and cross-database PK design."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - primary-keys
  - schema-design
  - uuid
  - autoincrement
  - sync
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
references:
  - https://www.sqlite.org/rowidtable.html
  - https://www.sqlite.org/autoinc.html
  - https://www.sqlite.org/withoutrowid.html
  - https://www.bytebase.com/blog/choose-primary-key-uuid-or-auto-increment/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - schema-design
---

# Primary key strategies

SQLite's primary key behavior is tied to its internal rowid mechanism. Choosing the right strategy affects performance, storage, and distributed sync compatibility.

## How SQLite's rowid works

Every SQLite table (unless `WITHOUT ROWID`) has a hidden 64-bit signed integer `rowid` that is the actual B-tree key. It is accessible via the aliases `rowid`, `_rowid_`, or `oid`. Rowids are not persistent — `VACUUM` may reassign them unless they are aliased by `INTEGER PRIMARY KEY`.

## Option 1: INTEGER PRIMARY KEY (recommended default)

```sql
CREATE TABLE findings (
    finding_id INTEGER PRIMARY KEY,
    content    TEXT NOT NULL
);
```

`INTEGER PRIMARY KEY` makes the column an alias for the rowid. There is no separate storage and no separate index — it is the fastest possible PK in SQLite.

On INSERT without a value, SQLite assigns `max(finding_id) + 1`. If the maximum row is deleted, that ID can be reused.

**Critical:** Only `INTEGER PRIMARY KEY` aliases rowid. `INT PRIMARY KEY` does NOT — it creates a regular column with a separate unique index, doubling storage overhead.

```sql
-- These alias rowid:
id INTEGER PRIMARY KEY
id INTEGER PRIMARY KEY NOT NULL  -- NOT NULL is redundant but harmless

-- These do NOT alias rowid:
id INT PRIMARY KEY         -- INT != INTEGER for this purpose
id INTEGER UNIQUE          -- UNIQUE != PRIMARY KEY for this purpose
```

## Option 2: INTEGER PRIMARY KEY AUTOINCREMENT

```sql
CREATE TABLE audit_entries (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action   TEXT NOT NULL
);
```

AUTOINCREMENT guarantees IDs are strictly monotonically increasing and never reused, even after row deletion. It maintains a counter in the internal `sqlite_sequence` table, which requires an extra read/write on every INSERT.

The official SQLite docs warn: *"AUTOINCREMENT imposes extra CPU, memory, disk space, and disk I/O overhead and should be avoided if not strictly needed."*

**Use AUTOINCREMENT only for:** audit logs, financial ledgers, event streams — where ID reuse is semantically wrong or a security concern. If the counter reaches `2^63 - 1`, further inserts fail with `SQLITE_FULL`.

## Option 3: UUID

UUIDs enable client-side ID generation without server coordination, which is essential for offline-first sync. Without UUIDs, two offline devices using autoincrement will produce identical IDs that collide on sync.

**Recommended: UUIDv7 (time-ordered)**

UUIDv7 encodes a Unix millisecond timestamp in the first 48 bits, making IDs roughly time-ordered. This preserves B-tree locality while maintaining global uniqueness. UUIDv4 (random) scatters inserts across the entire tree, causing page splits and cache thrashing.

```sql
-- Store UUIDv7 as BLOB for maximum efficiency (16 bytes vs 36 for TEXT)
CREATE TABLE distributed_events (
    event_id BLOB PRIMARY KEY,
    payload  TEXT NOT NULL
) WITHOUT ROWID;
```

**SQLite-specific note:** Unlike PostgreSQL, SQLite's clustered index is the rowid, not the PK column. A TEXT UUID primary key creates a separate B-tree — UUID randomness therefore causes less fragmentation than in PostgreSQL.

**For internal + external IDs, use a hybrid approach:**

```sql
CREATE TABLE resources (
    resource_id  INTEGER PRIMARY KEY,    -- fast internal FK target
    external_id  TEXT NOT NULL UNIQUE,  -- UUIDv7 for API / sync
    resource_name TEXT NOT NULL
);
```

**Never use `INTEGER PRIMARY KEY AUTOINCREMENT` for synced tables.** IDs will collide across devices.

## Option 4: WITHOUT ROWID

```sql
CREATE TABLE word_counts (
    word  TEXT PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0
) WITHOUT ROWID;
```

`WITHOUT ROWID` uses the declared PRIMARY KEY as the clustered index. The table is a single B-tree keyed on the PK columns — for the word_counts example, this means the word is stored once instead of twice (rowid B-tree + unique index), giving roughly 50% less disk space and 2x faster lookups.

**Use WITHOUT ROWID when:**
- The PK is non-integer or composite
- Rows are small (roughly < 50–200 bytes)
- The table does not store large strings or BLOBs

**Restrictions:**
- Must have an explicit PRIMARY KEY
- No AUTOINCREMENT
- `sqlite3_last_insert_rowid()` does not work
- Requires SQLite 3.8.2+

## Decision table

| Situation | Strategy |
|-----------|----------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Default / general tables | `INTEGER PRIMARY KEY` |
| Audit log or ledger — IDs must never reuse | `INTEGER PRIMARY KEY AUTOINCREMENT` |
| Distributed / multi-device sync | UUIDv7 as TEXT or BLOB |
| Exposing IDs in a public API | Separate UUID column + integer PK internally |
| Non-integer or composite key, small rows | `WITHOUT ROWID` |
| Maximum performance, local-only database | `INTEGER PRIMARY KEY` |

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
