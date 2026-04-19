---

id: 25A3B827-1DA9-4600-98EC-F5C492A162E3
title: "Schema evolution and migrations"
domain: agentic-cookbook://guidelines/implementing/data/schema-evolution
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Migration strategies for SQLite: PRAGMA user_version, ALTER TABLE limitations, the 12-step recreate procedure, and sync-compatible migration rules."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - migrations
  - schema-evolution
  - schema-design
  - sync
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
references:
  - https://sqlite.org/lang_altertable.html
  - https://david.rothlis.net/declarative-schema-migration-for-sqlite/
  - https://levlaz.org/sqlite-db-migrations-with-pragma-user_version/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - schema-design
---

# Schema evolution and migrations

## Track schema version with PRAGMA user_version

MUST use `PRAGMA user_version` to track schema version. It is a built-in 32-bit integer stored in the database file header — available immediately without querying any table.

```sql
-- Read current version
PRAGMA user_version;

-- Set version after applying a migration
PRAGMA user_version = 3;
```

Each migration file MUST end with the appropriate `PRAGMA user_version = N;` statement.

**Migration file structure:**

```
migrations/
  0001_initial_schema.sql
  0002_add_indexes.sql
  0003_add_fts.sql
```

**Python runner pattern:**

```python
current = db.execute('PRAGMA user_version').fetchone()[0]
for migration_file in sorted(migration_files):
    version = int(migration_file.split('_')[0])
    if version > current:
        db.executescript(open(migration_file).read())
```

Each migration MUST be wrapped in a transaction and MUST be idempotent (safe to run twice).

## ALTER TABLE limitations

SQLite's ALTER TABLE is severely limited. It supports:

- `ALTER TABLE x RENAME TO y`
- `ALTER TABLE x ADD COLUMN y` — column must allow NULL or have a DEFAULT
- `ALTER TABLE x RENAME COLUMN old TO new` (SQLite 3.25.0+)
- `ALTER TABLE x DROP COLUMN y` (SQLite 3.35.0+)

It does NOT support: changing column types, adding/removing constraints, changing DEFAULT values, or reordering columns.

**Backwards-compatible changes (safe to do directly):**

```sql
-- Add a nullable column
ALTER TABLE tasks ADD COLUMN priority TEXT;

-- Add a column with a default
ALTER TABLE tasks ADD COLUMN is_flagged INTEGER NOT NULL DEFAULT 0;

-- Create a new index
CREATE INDEX ix_tasks_priority ON tasks(priority);

-- Rename a column (SQLite 3.25.0+)
ALTER TABLE tasks RENAME COLUMN content TO description;
```

## The 12-step recreate procedure

For structural changes (changing column types, adding constraints, removing columns on old SQLite, reordering):

```sql
BEGIN TRANSACTION;
PRAGMA foreign_keys = OFF;

-- 1. Create the new table with the desired schema
CREATE TABLE tasks_new (
    task_id  INTEGER PRIMARY KEY,
    title    TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium'  -- was nullable, now required
);

-- 2. Copy data, transforming as needed
INSERT INTO tasks_new (task_id, title, priority)
SELECT task_id, title, COALESCE(priority, 'medium') FROM tasks;

-- 3. Drop the old table
DROP TABLE tasks;

-- 4. Rename the new table
ALTER TABLE tasks_new RENAME TO tasks;

-- 5. Recreate indexes, triggers, and views that referenced the old table
CREATE INDEX ix_tasks_priority ON tasks(priority);

-- 6. Verify referential integrity
PRAGMA foreign_key_check;

PRAGMA foreign_keys = ON;
COMMIT;
```

**Critical:** Disable foreign keys before the recreate and re-enable after. Run `foreign_key_check` before committing to catch any broken references.

## Sync-compatible migration rules

When SQLite databases sync with a server or between devices, schema migrations must be compatible across all participants — including devices that may be offline during rollout.

MUST follow these rules for any migration in a sync-capable schema:

1. **Only add columns — never remove or rename without a migration path.** A device on the old schema must be able to sync with the server on the new schema.
2. **New columns MUST have DEFAULT values.** CRDTs and merge logic require all columns to have a known value for all rows, including those written before the migration.
3. **Migrations MUST be idempotent.** A device may apply the same migration more than once if it reconnects after a partial sync.
4. **Wrap each migration in a transaction.** A failed migration must leave the database unchanged.
5. **Test migrations against databases at every previous version.** An offline device may skip multiple versions and apply them in sequence on reconnect.
6. **Always back up before migrating on the server side.**

**Migration tracking table (alternative to pragma for sync contexts):**

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    applied_date  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
```

Using a table instead of `PRAGMA user_version` allows the migration history to be synced to the server, giving visibility into which migrations each device has applied.

## Declarative migration approach

For projects where the schema is defined as a canonical DDL file, compare the actual database against an in-memory copy of the target schema:

1. Load the target schema into an in-memory SQLite database
2. Query `sqlite_schema` on both databases
3. Diff the two
4. Apply `ADD COLUMN`, `CREATE INDEX`, `CREATE TABLE` changes automatically
5. Flag column type changes or removals for manual SQL

This works well for additive changes and eliminates the need to write explicit `ADD COLUMN` migrations for new nullable columns.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
