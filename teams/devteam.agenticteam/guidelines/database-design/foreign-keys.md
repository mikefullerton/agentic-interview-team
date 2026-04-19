---

id: B16E64A4-462D-4F46-AFEB-1A06952E5E65
title: "Foreign keys and referential integrity"
domain: agentic-cookbook://guidelines/implementing/data/foreign-keys
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Enabling and declaring foreign keys in SQLite, ON DELETE/UPDATE actions, deferred constraints, indexing FK columns, and common pitfalls."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - foreign-keys
  - referential-integrity
  - schema-design
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
references:
  - https://sqlite.org/foreignkeys.html
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - schema-design
---

# Foreign keys and referential integrity

SQLite supports foreign key constraints but disables them by default. This is the most common SQLite pitfall: developers declare FK relationships, ship code, and discover constraints were silently never enforced.

## Enable foreign keys on every connection

```sql
PRAGMA foreign_keys = ON;
```

This MUST be executed on every database connection before any DML. It does not persist in the database file. It cannot be changed mid-transaction.

To verify the current state:

```sql
PRAGMA foreign_keys;  -- Returns 0 (off) or 1 (on)
```

## Declaring foreign keys

**Inline (column-level):**

```sql
CREATE TABLE tracks (
    track_id   INTEGER PRIMARY KEY,
    track_name TEXT NOT NULL,
    artist_id  INTEGER NOT NULL REFERENCES artists(artist_id)
);
```

**Table-level (required for composite FKs):**

```sql
CREATE TABLE songs (
    song_id     INTEGER PRIMARY KEY,
    song_artist TEXT NOT NULL,
    song_album  TEXT NOT NULL,
    FOREIGN KEY (song_artist, song_album)
        REFERENCES albums(album_artist, album_name)
);
```

The referenced column(s) MUST be the PRIMARY KEY or have a UNIQUE index. Otherwise, table creation fails.

## ON DELETE / ON UPDATE actions

Configure what happens to child rows when a referenced parent row is deleted or its key changes. Default is `NO ACTION`.

| Action | Behavior |
|--------|----------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| `NO ACTION` | Fail if child rows exist (checked at statement end) |
| `RESTRICT` | Fail immediately, even with deferred constraints |
| `SET NULL` | Set child FK column(s) to NULL |
| `SET DEFAULT` | Set child FK column(s) to their DEFAULT value |
| `CASCADE` | Delete children (ON DELETE) or propagate key change (ON UPDATE) |

```sql
CREATE TABLE tracks (
    track_id   INTEGER PRIMARY KEY,
    track_name TEXT NOT NULL,
    artist_id  INTEGER REFERENCES artists(artist_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);
```

`SET DEFAULT` will fail at runtime if the default value does not exist in the parent table. When using `SET DEFAULT`, ensure a row with the default value is always present.

## Deferred constraints

By default, FK constraints are checked at the end of each statement. Deferred constraints delay checking until `COMMIT`, which allows inserting in any order within a transaction:

```sql
CREATE TABLE tracks (
    track_id   INTEGER PRIMARY KEY,
    track_name TEXT NOT NULL,
    artist_id  INTEGER REFERENCES artists(artist_id)
        DEFERRABLE INITIALLY DEFERRED
);

BEGIN;
INSERT INTO tracks VALUES (1, 'My Song', 5);  -- artist 5 doesn't exist yet
INSERT INTO artists VALUES (5, 'New Artist'); -- now it does
COMMIT;                                        -- constraint checked here -- passes
```

For session-wide deferral during bulk imports or migrations:

```sql
PRAGMA defer_foreign_keys = ON;
```

## Index every FK column

Without an index on the child's FK column, every parent DELETE or UPDATE requires a full table scan of the child table. This is a silent performance trap.

```sql
-- Always create this index alongside the FK declaration
CREATE INDEX ix_tracks_artist_id ON tracks(artist_id);
```

## Common pitfalls

**NULL bypasses FK checks.** `NULL` in any FK column means no parent row is required — the constraint is not evaluated. If a FK column must always have a parent, declare it `NOT NULL`.

**`INT PRIMARY KEY` vs `INTEGER PRIMARY KEY`.** Only the exact keyword `INTEGER` creates a rowid alias. `INT` creates a regular column. Referenced columns must be the PK or have a UNIQUE index.

**Composite FKs must match exactly.** Column count, types, and collation must match the parent's PRIMARY KEY or UNIQUE constraint precisely.

**ALTER TABLE restrictions.** You cannot add a column with a FK constraint and a non-NULL default:

```sql
-- Fails
ALTER TABLE tracks ADD COLUMN genre_id INTEGER NOT NULL DEFAULT 1
    REFERENCES genres(genre_id);

-- Works (NULL default is allowed)
ALTER TABLE tracks ADD COLUMN genre_id INTEGER REFERENCES genres(genre_id);
```

**Cross-schema FKs are not supported.** Foreign keys cannot reference tables in attached databases.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
