---
title: "Schema Design"
domain: database
type: guideline
status: draft
created: 2026-04-03
modified: 2026-04-06
author: Mike Fullerton
summary: "Column naming, data types, primary keys, foreign keys, constraints, and schema design patterns for SQLite"
platforms:
  - sqlite
tags:
  - database
  - sqlite
  - schema-design
references:
  - https://sqlite.org/docs.html
  - https://sqlite.org/foreignkeys.html
  - https://sqlite.org/stricttables.html
  - https://sqlite.org/rowidtable.html
  - https://sqlite.org/autoinc.html
  - https://sqlite.org/withoutrowid.html
related:
  - performance-and-tuning.md
  - operations-and-maintenance.md
---

# Schema Design

> Column naming conventions, data types, primary key strategies, foreign keys, constraints, and schema design patterns for SQLite.

---

## 1. Column Naming Conventions

### Recommended Practice: snake_case everywhere

Use `snake_case` for all identifiers -- tables, columns, indexes, constraints, triggers. This is the dominant convention in SQL and the most readable across tools and contexts.

**Rationale:** SQL is case-insensitive for identifiers. CamelCase creates ambiguity: `UnderValue` and `Undervalue` are identical to SQLite, but `under_value` and `undervalue` are visually distinct. Underscores also improve readability for non-native English speakers and people with vision difficulties.

```sql
-- Good
CREATE TABLE workflow_run (
    workflow_run_id  INTEGER PRIMARY KEY,
    workflow_name    TEXT NOT NULL,
    creation_date    TEXT NOT NULL DEFAULT (datetime('now')),
    is_active        INTEGER NOT NULL DEFAULT 1
);

-- Avoid
CREATE TABLE WorkflowRun (
    WorkflowRunID INTEGER PRIMARY KEY,
    WorkflowName  TEXT NOT NULL,
    CreatedAt     TEXT NOT NULL DEFAULT (datetime('now')),
    IsActive      INTEGER NOT NULL DEFAULT 1
);
```

### Table Naming: Plural vs. Singular

Both conventions have advocates. The key argument for **plural** is that it avoids collisions with SQL reserved words (`user` is reserved; `users` is not). The key argument for **singular** is that each row represents one entity, and singular nouns compose better in compound names (`workflow_run` vs. `workflows_runs`).

**Pick one and be consistent.** If a project already uses singular, stick with singular.

### Primary Key Column Naming

Use `table_name_id` (or at minimum a descriptive name), not bare `id`.

```sql
-- Good: self-documenting in JOINs
SELECT *
FROM audit_log al
JOIN actors a ON a.actor_id = al.changed_by_actor_id;

-- Bad: ambiguous in JOINs, easy to introduce bugs
SELECT *
FROM audit_log al
JOIN actors a ON a.id = al.changed_by;
```

When both sides of a JOIN say `id`, errors are invisible. When they say `actor_id` and `finding_id`, mismatches are obvious.

### Foreign Key Column Naming

Match the referenced column name when possible. When a table references the same parent table multiple times, add a descriptive qualifier:

```sql
-- Single reference: match the parent column name
finding_id INTEGER REFERENCES findings(finding_id)

-- Multiple references to same parent: add qualifier
source_actor_id      INTEGER REFERENCES actors(actor_id),
destination_actor_id INTEGER REFERENCES actors(actor_id)
```

### Boolean Columns

Prefix with `is_` or `has_`:

```sql
is_active    INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
has_children INTEGER NOT NULL DEFAULT 0 CHECK (has_children IN (0, 1))
```

### Date/Time Columns

Use descriptive event names, not generic suffixes:

```sql
-- Good: describes the event
creation_date    TEXT NOT NULL DEFAULT (datetime('now')),
modification_date TEXT,
completion_date  TEXT

-- Avoid: vague
created_at TEXT,
updated_at TEXT
```

### Reserved Words to Avoid

SQLite has 147 reserved keywords. Common traps for column/table names:

| Dangerous Name | Problem | Alternative |
|---|---|---|
| `order` | Reserved keyword | `sort_order`, `display_order` |
| `group` | Reserved keyword | `team`, `grouping` |
| `index` | Reserved keyword | `position`, `sort_index` |
| `key` | Reserved keyword | `lookup_key`, `api_key` |
| `value` | Reserved keyword | `setting_value`, `metric_value` |
| `action` | Reserved keyword | `operation`, `activity` |
| `check` | Reserved keyword | `validation`, `check_result` |
| `column` | Reserved keyword | `field`, `attribute` |
| `default` | Reserved keyword | `default_value`, `fallback` |
| `replace` | Reserved keyword | `substitution`, `replacement` |
| `match` | Reserved keyword | `comparison`, `match_result` |
| `plan` | Reserved keyword | `execution_plan` |
| `query` | Reserved keyword | `search_query` |
| `row` | Reserved keyword | `record`, `entry` |
| `filter` | Reserved keyword | `criterion`, `filter_expr` |

If you must use a reserved word, quote it with double quotes (`"order"`), but this adds friction to every query. Better to choose a different name.

**Future-proofing:** SQLite adds new keywords over time. The official docs recommend quoting any English word used as an identifier, even if it is not currently reserved.

### Index and Constraint Naming

```sql
-- Indexes: ix_tablename_purpose
CREATE INDEX ix_findings_workflow_run_id ON findings(workflow_run_id);
CREATE UNIQUE INDEX ux_actors_email ON actors(email);

-- Triggers: tr_tablename_event_purpose
CREATE TRIGGER tr_documents_after_update_audit ...

-- Check constraints: ck_tablename_column
CONSTRAINT ck_employees_salary CHECK (salary > 0)
```

### Sources

- [Database Naming Standards (Ovid)](https://dev.to/ovid/database-naming-standards-2061) -- snake_case rationale, plural tables, FK naming
- [SQL Naming Conventions (bbkane)](https://www.bbkane.com/blog/sql-naming-conventions/) -- PK naming, index conventions, trigger naming
- [SQLite Keywords](https://www.sqlite.org/lang_keywords.html) -- official keyword list, quoting rules
- [Baeldung SQL Naming Conventions](https://www.baeldung.com/sql/database-table-column-naming-conventions)
- [BrainStation SQL Naming Conventions](https://brainstation.io/learn/sql/naming-conventions)

---

## 2. Data Types and Type Affinity

### SQLite's Type System is Unique

Most databases use **static typing** -- the column determines the type. SQLite uses **dynamic typing** -- the value determines the type. A column's declared type is a *preference* (called "affinity"), not a constraint.

```sql
-- This is legal in SQLite (without STRICT):
CREATE TABLE demo (age INTEGER);
INSERT INTO demo VALUES ('not a number');  -- Stores as TEXT
SELECT typeof(age) FROM demo;             -- Returns 'text'
```

### The Five Storage Classes

Every value in SQLite belongs to exactly one storage class:

| Storage Class | Description | Size |
|---|---|---|
| `NULL` | Null value | 0 bytes |
| `INTEGER` | Signed integer | 0, 1, 2, 3, 4, 6, or 8 bytes (variable) |
| `REAL` | IEEE 754 float | 8 bytes |
| `TEXT` | UTF-8 string | Variable |
| `BLOB` | Raw bytes | Variable |

**Key differences from other databases:**
- No `BOOLEAN` type. Use `INTEGER` with 0/1. `TRUE` and `FALSE` keywords (since 3.23.0) are just aliases for 1 and 0.
- No `DATE`/`DATETIME` type. Store as `TEXT` (ISO 8601: `'YYYY-MM-DD HH:MM:SS'`), `REAL` (Julian day), or `INTEGER` (Unix timestamp). TEXT is recommended for readability.
- `INTEGER` storage is variable-width (0-8 bytes), not fixed. Small values use less space than large ones.

### Type Affinity: The 5-Rule Algorithm

For non-STRICT tables, SQLite determines column affinity from the declared type name using these rules **in order of precedence**:

| Rule | If declared type contains... | Affinity | Examples |
|---|---|---|---|
| 1 | `"INT"` | INTEGER | INT, INTEGER, TINYINT, SMALLINT, MEDIUMINT, BIGINT, INT2, INT8 |
| 2 | `"CHAR"`, `"CLOB"`, `"TEXT"` | TEXT | CHARACTER(20), VARCHAR(255), NCHAR, TEXT, CLOB |
| 3 | `"BLOB"` or no type | BLOB | BLOB, (no type specified) |
| 4 | `"REAL"`, `"FLOA"`, `"DOUB"` | REAL | REAL, DOUBLE, FLOAT, DOUBLE PRECISION |
| 5 | Otherwise | NUMERIC | NUMERIC, DECIMAL(10,5), BOOLEAN, DATE, DATETIME |

**Critical: order matters.** `"CHARINT"` matches both rules 1 and 2, but rule 1 wins -- affinity is INTEGER. `"FLOATING POINT"` contains `"INT"` (in "POINT"), so affinity is INTEGER, not REAL.

### The STRING Gotcha

Declaring a column as `STRING` gives it **NUMERIC** affinity (rule 5 -- "STRING" does not contain "CHAR", "CLOB", or "TEXT"). This means number-like strings get silently converted to integers:

```sql
CREATE TABLE demo (val STRING);
INSERT INTO demo VALUES ('007');
SELECT typeof(val), val FROM demo;
-- Returns: integer, 7  (leading zeros lost!)
```

**Fix:** Use `TEXT`, never `STRING`.

### NUMERIC Affinity Behavior

NUMERIC affinity aggressively converts text to numbers:

```sql
CREATE TABLE demo (val NUMERIC);
INSERT INTO demo VALUES ('3.0e+5');
SELECT typeof(val), val FROM demo;
-- Returns: integer, 300000  (converted from scientific notation to integer)
```

### Comparison Pitfalls

When comparing values of different storage classes without affinity guidance, SQLite uses this ordering: `NULL < INTEGER/REAL < TEXT < BLOB`. This produces surprising results:

```sql
CREATE TABLE t1 (
    a TEXT,     -- text affinity
    b NUMERIC,  -- numeric affinity
    c BLOB,     -- blob affinity (no type)
    d           -- blob affinity (no type)
);
INSERT INTO t1 VALUES ('500', '500', '500', 500);

-- Column c has BLOB affinity, d is integer 500.
-- Without affinity guidance: INTEGER < TEXT always
SELECT d < '40' FROM t1;
-- Returns: 1  (integer 500 is "less than" text '40')
```

The full comparison rules:
1. If one operand has INTEGER/REAL/NUMERIC affinity and the other has TEXT/BLOB/no affinity, apply NUMERIC affinity to the other operand before comparing.
2. If one operand has TEXT affinity and the other has no affinity, apply TEXT affinity to the other operand.
3. Otherwise, compare as-is using the storage class ordering.

### STRICT Tables (SQLite 3.37.0+)

STRICT tables enforce rigid typing. Declare with the `STRICT` keyword:

```sql
CREATE TABLE measurements (
    measurement_id INTEGER PRIMARY KEY,
    sensor_name    TEXT NOT NULL,
    reading        REAL NOT NULL,
    raw_data       BLOB
) STRICT;
```

**Allowed types in STRICT tables:** `INT`, `INTEGER`, `REAL`, `TEXT`, `BLOB`, `ANY`.

**Behavior:**
- Inserting a wrong type raises `SQLITE_CONSTRAINT_DATATYPE`
- SQLite attempts type coercion first (like other databases), fails if coercion fails
- `INTEGER PRIMARY KEY` still aliases rowid (but `INT PRIMARY KEY` does not)
- `ANY` type preserves values exactly as inserted, with no coercion

```sql
CREATE TABLE demo (val ANY) STRICT;
INSERT INTO demo VALUES ('007');
SELECT typeof(val), val FROM demo;
-- Returns: text, 007  (preserved exactly -- no conversion)

CREATE TABLE demo2 (val INTEGER) STRICT;
INSERT INTO demo2 VALUES ('not a number');
-- ERROR: SQLITE_CONSTRAINT_DATATYPE
```

**Combining with WITHOUT ROWID:**
```sql
CREATE TABLE lookups (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
) STRICT, WITHOUT ROWID;
```

**Compatibility:** Databases with STRICT tables cannot be opened by SQLite versions before 3.37.0.

### Practical Recommendations

1. **Declare explicit types** on every column, even in non-STRICT tables. Use `TEXT`, `INTEGER`, `REAL`, `BLOB` -- the four canonical storage classes.
2. **Never use `STRING`** -- it gives NUMERIC affinity. Use `TEXT`.
3. **Use `TEXT` for dates** in ISO 8601 format (`'YYYY-MM-DD HH:MM:SS'`). It sorts correctly and is human-readable.
4. **Use `INTEGER` for booleans** with CHECK constraints: `CHECK (col IN (0, 1))`.
5. **Consider STRICT tables** for new schemas where type safety matters. The tradeoff is losing compatibility with SQLite < 3.37.0.
6. **Be explicit about comparisons** -- don't rely on affinity coercion in WHERE clauses. Cast or quote consistently.

### Sources

- [Datatypes In SQLite](https://www.sqlite.org/datatype3.html) -- official type system docs, affinity rules, comparison behavior
- [STRICT Tables](https://www.sqlite.org/stricttables.html) -- official STRICT table docs
- [The Advantages of Flexible Typing](https://www.sqlite.org/flextypegood.html) -- official rationale for dynamic typing
- [SQLite's Flexible Typing (DEV Community)](https://dev.to/lovestaco/sqlites-flexible-typing-storage-types-and-column-affinity-4ggg)
- [Understanding Type Affinity in SQLite](https://database.guide/understanding-type-affinity-in-sqlite/)

---

## 3. Primary Key Strategies

### How SQLite's rowid Works

Every SQLite table (unless `WITHOUT ROWID`) has a hidden 64-bit signed integer `rowid`. It is:
- The actual key used by the B-tree storage engine
- Accessible via the aliases `rowid`, `_rowid_`, or `oid` (unless a real column shadows these names)
- Automatically assigned on INSERT if not specified
- **Not persistent** -- `VACUUM` may reassign rowids unless aliased by `INTEGER PRIMARY KEY`

### Option 1: INTEGER PRIMARY KEY (Recommended Default)

```sql
CREATE TABLE findings (
    finding_id INTEGER PRIMARY KEY,
    content    TEXT NOT NULL,
    severity   TEXT NOT NULL
);
```

**What happens:**
- `finding_id` becomes an **alias for rowid** -- no extra storage, no separate index
- On INSERT without a value, SQLite assigns `max(finding_id) + 1`
- If the max row is deleted, that ID *can* be reused
- This is the fastest possible primary key in SQLite

**Critical detail:** Only `INTEGER PRIMARY KEY` aliases rowid. `INT PRIMARY KEY` does NOT -- it creates a regular column with a separate unique index, doubling storage overhead.

```sql
-- These alias rowid (identical behavior):
id INTEGER PRIMARY KEY
id INTEGER PRIMARY KEY NOT NULL  -- NOT NULL is redundant but harmless

-- These do NOT alias rowid:
id INT PRIMARY KEY        -- INT != INTEGER for this purpose
id INTEGER PRIMARY KEY DESC  -- DESC prevents aliasing (since SQLite 3.45.0 this may change)
id INTEGER UNIQUE         -- UNIQUE != PRIMARY KEY for this purpose
```

### Option 2: INTEGER PRIMARY KEY AUTOINCREMENT

```sql
CREATE TABLE audit_entries (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action   TEXT NOT NULL,
    actor_id INTEGER NOT NULL
);
```

**What it adds beyond plain INTEGER PRIMARY KEY:**
- Guarantees IDs are **strictly monotonically increasing and never reused** -- even if the highest row is deleted
- Maintains a counter in the internal `sqlite_sequence` table
- If the counter reaches `2^63 - 1` (9,223,372,036,854,775,807), further inserts fail with `SQLITE_FULL`
- Without AUTOINCREMENT, SQLite would try random IDs at the max, potentially reusing old ones

**Performance cost:** Every INSERT requires an additional read/write to `sqlite_sequence`. The official SQLite docs explicitly warn: *"The AUTOINCREMENT keyword imposes extra CPU, memory, disk space, and disk I/O overhead and should be avoided if not strictly needed."*

**When to use it:** Audit logs, financial ledgers, event streams -- anywhere ID reuse would be semantically wrong or a security concern.

### Option 3: UUID

```sql
-- Text form (36 chars, human-readable but large)
CREATE TABLE sync_records (
    record_id TEXT PRIMARY KEY,
    data      TEXT NOT NULL
);

-- Blob form (16 bytes, more compact)
CREATE TABLE sync_records (
    record_id BLOB PRIMARY KEY,
    data      TEXT NOT NULL
);
```

**Advantages:**
- Globally unique across databases, servers, devices
- Generated client-side -- ID is known before INSERT
- No coordination required in distributed systems

**Significant downsides in SQLite:**
- Random UUIDs (v4) destroy B-tree locality. Sequential integer inserts append to the rightmost leaf page; random UUIDs scatter inserts across the entire tree, causing page splits and cache thrashing.
- 36-byte TEXT UUID is 9x larger than an 8-byte integer. This ripples into every foreign key and index.
- Does not alias rowid, so SQLite maintains two data structures (the rowid B-tree and a separate index).

**UUIDv7 mitigates the locality problem.** UUIDv7 (IETF-approved May 2024) encodes a Unix millisecond timestamp in the first 48 bits, making IDs time-ordered. This preserves B-tree locality while maintaining global uniqueness.

```sql
-- Store UUIDv7 as BLOB for maximum efficiency
CREATE TABLE distributed_events (
    event_id BLOB PRIMARY KEY,  -- 16-byte UUIDv7
    payload  TEXT NOT NULL
) WITHOUT ROWID;
```

**Hybrid approach:** Use `INTEGER PRIMARY KEY` for internal operations (joins, indexes, foreign keys) and a separate UUID column for external APIs:

```sql
CREATE TABLE resources (
    resource_id  INTEGER PRIMARY KEY,
    external_id  TEXT NOT NULL UNIQUE,  -- UUIDv7 for API exposure
    resource_name TEXT NOT NULL
);
```

### WITHOUT ROWID Tables

```sql
CREATE TABLE word_counts (
    word TEXT PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0
) WITHOUT ROWID;
```

**What it does:** Uses the declared PRIMARY KEY as the clustered index key instead of a hidden rowid. The table is stored as a single B-tree keyed on the PRIMARY KEY columns.

**When to use:**
- Non-integer or composite primary keys
- Small rows (< ~1/20th of page size, roughly 50-200 bytes)
- Tables that do NOT store large strings or BLOBs

**Performance benefit:** For the `word_counts` example, a regular table stores the word text twice (once in the rowid B-tree, once in the unique index). WITHOUT ROWID stores it once -- roughly **50% less disk space and 2x faster** for simple lookups.

**Restrictions:**
- Must have an explicit PRIMARY KEY (error if omitted)
- No AUTOINCREMENT
- NOT NULL enforced on all PRIMARY KEY columns (SQL standard)
- `sqlite3_last_insert_rowid()` does not work
- No incremental BLOB I/O
- Requires SQLite 3.8.2+

### Decision Table

| Situation | Use |
|---|---|
| Default / general tables | `INTEGER PRIMARY KEY` |
| Audit log, ledger -- IDs must never reuse | `INTEGER PRIMARY KEY AUTOINCREMENT` |
| Distributed / multi-device sync | UUIDv7 as `BLOB` (prefer WITHOUT ROWID) |
| Exposing IDs in a public API | Separate UUID column + integer PK internally |
| Non-integer or composite key, small rows | `WITHOUT ROWID` |
| Maximum performance, local-only DB | `INTEGER PRIMARY KEY` |

### Sources

- [Rowid Tables](https://www.sqlite.org/rowidtable.html) -- official rowid behavior, INTEGER PRIMARY KEY aliasing
- [SQLite Autoincrement](https://www.sqlite.org/autoinc.html) -- official AUTOINCREMENT docs, sqlite_sequence, performance warnings
- [WITHOUT ROWID Tables](https://www.sqlite.org/withoutrowid.html) -- official WITHOUT ROWID docs, when to use, restrictions
- [UUID vs Auto-Increment (Bytebase)](https://www.bytebase.com/blog/choose-primary-key-uuid-or-auto-increment/) -- UUID performance analysis, UUIDv7
- [Primary Key Data Types (High Performance SQLite)](https://highperformancesqlite.com/watch/primary-key-data-types)

---

## 4. Foreign Keys and Referential Integrity

### The Critical First Step: Enable Foreign Keys

Foreign key constraints are **disabled by default** in SQLite and must be enabled for **each database connection** at runtime:

```sql
PRAGMA foreign_keys = ON;
```

This is the single most common SQLite pitfall. Developers create schemas with FOREIGN KEY declarations, test them, and find constraints are silently not enforced. The PRAGMA does not persist in the database file -- it must be set every time a connection opens.

**Verification:**
```sql
PRAGMA foreign_keys;  -- Returns 0 (off) or 1 (on)
```

**Cannot be changed mid-transaction:** Attempting to enable/disable foreign keys inside a `BEGIN...COMMIT` block silently does nothing.

**Why this design?** Foreign keys were added long after SQLite's file format was designed. There is no place in the database file to store the on/off state, and changing the default would break billions of existing applications.

### Foreign Key Declaration

```sql
-- Inline (column-level)
CREATE TABLE tracks (
    track_id     INTEGER PRIMARY KEY,
    track_name   TEXT NOT NULL,
    artist_id    INTEGER NOT NULL REFERENCES artists(artist_id)
);

-- Table-level (required for composite FKs)
CREATE TABLE songs (
    song_id     INTEGER PRIMARY KEY,
    song_artist TEXT NOT NULL,
    song_album  TEXT NOT NULL,
    FOREIGN KEY (song_artist, song_album)
        REFERENCES albums(album_artist, album_name)
);
```

**Requirement:** The referenced column(s) must be the PRIMARY KEY or have a UNIQUE index. Otherwise, the table creation fails.

### ON DELETE / ON UPDATE Actions

Actions configure what happens to child rows when a referenced parent row is deleted or its key is modified. Default is `NO ACTION`.

| Action | Behavior |
|---|---|
| `NO ACTION` | Fail if child rows exist (checked at statement end) |
| `RESTRICT` | Fail immediately, even with deferred constraints |
| `SET NULL` | Set child FK column(s) to NULL |
| `SET DEFAULT` | Set child FK column(s) to their DEFAULT value |
| `CASCADE` | Delete child rows (ON DELETE) or update child FK values (ON UPDATE) |

```sql
CREATE TABLE tracks (
    track_id   INTEGER PRIMARY KEY,
    track_name TEXT NOT NULL,
    artist_id  INTEGER REFERENCES artists(artist_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);
```

**CASCADE example:**
```sql
-- Parent table
INSERT INTO artists VALUES (1, 'Dean Martin');
INSERT INTO artists VALUES (2, 'Frank Sinatra');

-- Child rows
INSERT INTO tracks VALUES (11, 'That''s Amore', 1);
INSERT INTO tracks VALUES (12, 'Christmas Blues', 1);
INSERT INTO tracks VALUES (13, 'My Way', 2);

-- Update parent key -- cascades to all children
UPDATE artists SET artist_id = 100 WHERE artist_name = 'Dean Martin';

-- After: tracks 11 and 12 now have artist_id = 100
```

**SET DEFAULT pitfall:** If the default value does not exist in the parent table, the action fails:

```sql
CREATE TABLE tracks (
    track_id   INTEGER PRIMARY KEY,
    track_name TEXT NOT NULL,
    artist_id  INTEGER DEFAULT 0 REFERENCES artists(artist_id)
        ON DELETE SET DEFAULT
);

-- This FAILS if artist_id=0 doesn't exist in artists
DELETE FROM artists WHERE artist_id = 3;
-- Error: foreign key constraint failed

-- Fix: ensure the default value exists
INSERT INTO artists VALUES (0, 'Unknown Artist');
-- Now the delete succeeds
```

### Deferred Constraints

By default, FK constraints are checked at the end of each statement (immediate). Deferred constraints delay checking until COMMIT:

```sql
CREATE TABLE tracks (
    track_id   INTEGER PRIMARY KEY,
    track_name TEXT NOT NULL,
    artist_id  INTEGER REFERENCES artists(artist_id)
        DEFERRABLE INITIALLY DEFERRED
);

-- With deferred constraints, insert order doesn't matter within a transaction:
BEGIN;
INSERT INTO tracks VALUES (1, 'My Song', 5);  -- artist 5 doesn't exist yet
INSERT INTO artists VALUES (5, 'New Artist');  -- now it does
COMMIT;  -- constraint checked here -- passes
```

**Temporary override** for all constraints in a session:
```sql
PRAGMA defer_foreign_keys = ON;
```

This is useful for bulk data imports or schema migrations where insert order is inconvenient.

### Common Pitfalls

**1. NULL values bypass FK checks:**
```sql
-- This succeeds even if artist_id=999 doesn't exist
INSERT INTO tracks (track_id, track_name, artist_id) VALUES (1, 'Test', NULL);
-- NULL in any FK column = no parent row required
```

**2. Missing indexes on child FK columns:**
Without an index on the child's FK column, every parent DELETE/UPDATE requires a full table scan of the child table:

```sql
-- Always create indexes on FK columns
CREATE INDEX ix_tracks_artist_id ON tracks(artist_id);
```

**3. Composite FKs must match exactly:**
The child column count, types, and collation must match the parent's PRIMARY KEY or UNIQUE constraint exactly.

**4. ALTER TABLE restrictions:**
You cannot add a new column with a FK constraint and a non-NULL default:

```sql
-- Fails
ALTER TABLE tracks ADD COLUMN genre_id INTEGER NOT NULL DEFAULT 1
    REFERENCES genres(genre_id);

-- Works (NULL default)
ALTER TABLE tracks ADD COLUMN genre_id INTEGER REFERENCES genres(genre_id);
```

**5. Cross-schema FKs not supported:**
Foreign keys cannot reference tables in attached databases.

### Sources

- [SQLite Foreign Key Support](https://sqlite.org/foreignkeys.html) -- official comprehensive FK docs
- [SQLite Forum: Why is FK support per-connection?](https://sqlite.org/forum/info/c5dc50f61b88c587) -- design rationale
- [SQLite Foreign Keys: Common Pitfalls](https://runebook.dev/en/docs/sqlite/foreignkeys) -- indexed practical guide

---

## 5. CHECK Constraints and Data Validation

### Syntax

```sql
-- Inline (column-level)
CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    quantity     INTEGER NOT NULL CHECK (quantity >= 0),
    price        REAL NOT NULL CHECK (price > 0)
);

-- Table-level (can reference multiple columns)
CREATE TABLE events (
    event_id   INTEGER PRIMARY KEY,
    start_date TEXT NOT NULL,
    end_date   TEXT NOT NULL,
    CHECK (end_date >= start_date)
);

-- Named constraint
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    salary      REAL NOT NULL,
    CONSTRAINT ck_employees_salary CHECK (salary > 0)
);
```

There is no functional difference between column-level and table-level CHECK constraints. The only advantage of table-level is the ability to reference multiple columns.

### How CHECK Evaluation Works

1. The CHECK expression is evaluated on every INSERT and UPDATE
2. The result is cast to NUMERIC
3. **If result is integer 0 or real 0.0** -- constraint violation (`SQLITE_CONSTRAINT_CHECK`)
4. **If result is NULL** -- no violation (NULL is truthy for CHECK purposes)
5. **If result is any non-zero value** -- no violation

**The NULL gotcha:** `CHECK (status IN ('active', 'inactive'))` allows NULL values because `NULL IN (...)` evaluates to NULL, which is not zero. Add `NOT NULL` separately if NULL should be prohibited.

### Common Validation Patterns

#### Range Validation
```sql
age     INTEGER NOT NULL CHECK (age >= 0 AND age <= 150),
score   REAL NOT NULL CHECK (score BETWEEN 0.0 AND 100.0),
percent INTEGER NOT NULL CHECK (percent >= 0 AND percent <= 100)
```

#### Enum-Like Constraints (Restricting to Known Values)
```sql
status    TEXT NOT NULL CHECK (status IN ('pending', 'active', 'completed', 'failed')),
priority  INTEGER NOT NULL CHECK (priority IN (1, 2, 3, 4, 5)),
direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound'))
```

#### Boolean Enforcement
```sql
is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
```

#### Pattern Matching
```sql
email TEXT NOT NULL CHECK (email LIKE '%_@_%.__%'),
phone TEXT CHECK (phone LIKE '+%' OR phone IS NULL),
code  TEXT NOT NULL CHECK (length(code) = 6 AND code GLOB '[A-Z][A-Z][0-9][0-9][0-9][0-9]')
```

#### Multi-Column Constraints
```sql
CREATE TABLE promotions (
    promotion_id INTEGER PRIMARY KEY,
    start_date   TEXT NOT NULL,
    end_date     TEXT NOT NULL,
    discount     REAL NOT NULL,
    CHECK (end_date > start_date),
    CHECK (discount > 0 AND discount <= 1.0)
);
```

#### Conditional Logic
```sql
CREATE TABLE inventory (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    stock        INTEGER NOT NULL,
    status       TEXT NOT NULL,
    CHECK (
        (status = 'surplus' AND stock >= 500) OR
        (status != 'surplus')
    )
);
```

#### String Length Validation
```sql
username TEXT NOT NULL CHECK (length(username) >= 3 AND length(username) <= 50),
api_key  TEXT NOT NULL CHECK (length(api_key) = 32)
```

### What Is NOT Allowed in CHECK Expressions

These are explicitly prohibited and will cause errors:

| Prohibited | Reason |
|---|---|
| Subqueries (`SELECT ...`) | Cannot reference other rows or tables |
| `CURRENT_TIME` | Non-deterministic |
| `CURRENT_DATE` | Non-deterministic |
| `CURRENT_TIMESTAMP` | Non-deterministic |

**Workaround for date validation:** You cannot use `CHECK (event_date <= CURRENT_DATE)` in the schema definition. However, `DEFAULT (datetime('now'))` works for defaults because defaults are evaluated at INSERT time, not at schema creation time.

For date validation that depends on "now", use triggers or application-level validation instead.

### Conflict Resolution

The conflict resolution algorithm for CHECK constraints is always `ABORT`. The `ON CONFLICT` clause is parsed for historical compatibility but has no effect:

```sql
-- ON CONFLICT is ignored for CHECK constraints
quantity INTEGER NOT NULL CHECK (quantity >= 0) ON CONFLICT REPLACE
-- Still ABORTs on violation, does NOT replace
```

### Disabling CHECK Constraints

For data migrations or imports of potentially dirty data:

```sql
PRAGMA ignore_check_constraints = ON;
-- Import data...
PRAGMA ignore_check_constraints = OFF;
```

After import, verify data integrity:

```sql
PRAGMA integrity_check;  -- Reports CHECK violations as corruption
```

### Limitations

1. **Cannot add via ALTER TABLE.** You must recreate the table:
   ```sql
   -- 1. Create new table with constraints
   CREATE TABLE new_table (...constraints...);
   -- 2. Copy data
   INSERT INTO new_table SELECT * FROM old_table;
   -- 3. Drop old table
   DROP TABLE old_table;
   -- 4. Rename
   ALTER TABLE new_table RENAME TO old_table;
   ```

2. **Row-scoped only.** Cannot validate against other rows (use triggers for cross-row validation).

3. **Not verified on SELECT.** Corrupted data (from external file manipulation or disabled checks) can be read even if it violates constraints.

4. **Minimal performance impact.** CHECK expressions are simple comparisons evaluated in-process. Modern SQLite versions have optimized constraint evaluation. The cost is negligible compared to disk I/O.

### Sources

- [CREATE TABLE: CHECK constraints](https://www.sqlite.org/lang_createtable.html) -- official docs, evaluation rules, prohibited expressions
- [Validating Data with SQLite CHECK Constraints (Sling Academy)](https://www.slingacademy.com/article/validating-your-data-with-sqlite-check-constraints/)
- [How to Write Effective CHECK Constraints (Sling Academy)](https://www.slingacademy.com/article/how-to-write-effective-check-constraints-in-sqlite/)
- [SQLite Check Constraints (sql-easy.com)](https://www.sql-easy.com/learn/sqlite-check-constraints/)
- [SQLite Data Validation: Using CHECK and Alternatives](https://runebook.dev/en/docs/sqlite/lang_createtable/ckconst)

---

## 6. Schema Design Patterns

### Polymorphic Foreign Keys

#### The Problem

A polymorphic foreign key is a column that references one of several different tables. A common example is a `changed_by` column in an audit log where the actor could be a human, a service, or a bot.

#### Pattern 1: Generic FK with Discriminator Column

```sql
CREATE TABLE audit_log (
    audit_log_id    INTEGER PRIMARY KEY,
    changed_by_id   INTEGER NOT NULL,
    changed_by_type TEXT NOT NULL CHECK (changed_by_type IN ('human', 'service', 'bot'))
);
```

Store both the `id` and a `type` discriminator. Application code resolves the join. SQLite will not enforce FK referential integrity across multiple tables even with `PRAGMA foreign_keys = ON`, so the app layer owns that constraint.

**Pros:** Simple, works everywhere, no schema changes when adding types
**Cons:** No DB-level FK enforcement, easy to get into inconsistent state

#### Pattern 2: Supertype / Base Table (Recommended)

```sql
CREATE TABLE actors (
    actor_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_type   TEXT NOT NULL CHECK (actor_type IN ('human', 'service', 'bot')),
    display_name TEXT NOT NULL  -- denormalized for fast queries
);

CREATE TABLE humans (
    actor_id INTEGER PRIMARY KEY REFERENCES actors(actor_id),
    name     TEXT NOT NULL,
    email    TEXT NOT NULL UNIQUE
);

CREATE TABLE services (
    actor_id     INTEGER PRIMARY KEY REFERENCES actors(actor_id),
    service_name TEXT NOT NULL,
    api_key_hint TEXT
);

CREATE TABLE bots (
    actor_id       INTEGER PRIMARY KEY REFERENCES actors(actor_id),
    bot_name       TEXT NOT NULL,
    owner_actor_id INTEGER REFERENCES actors(actor_id)
);

CREATE TABLE audit_log (
    audit_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name   TEXT NOT NULL,
    row_id       INTEGER NOT NULL,
    operation    TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    changed_by   INTEGER NOT NULL REFERENCES actors(actor_id),
    change_date  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

`audit_log.changed_by` is a **real, enforced FK** into `actors`. Each subtype has its own table with a 1:1 FK back to `actors`.

**Pros:** True referential integrity, clean join point, scalable query pattern
**Cons:** Extra join to get subtype-specific data, insert order matters (supertype first)

#### Pattern 3: Nullable Column Per Type

```sql
CREATE TABLE audit_log (
    audit_log_id           INTEGER PRIMARY KEY,
    changed_by_human_id    INTEGER REFERENCES humans(actor_id),
    changed_by_service_id  INTEGER REFERENCES services(actor_id),
    changed_by_bot_id      INTEGER REFERENCES bots(actor_id),
    CHECK (
        (changed_by_human_id   IS NOT NULL) +
        (changed_by_service_id IS NOT NULL) +
        (changed_by_bot_id     IS NOT NULL) = 1
    )
);
```

**Pros:** Real FK enforcement on each column, fully declarative
**Cons:** Gets unwieldy fast as types grow, adds nullable columns

#### Recommendation

**Use Pattern 2 (supertype table)** when actor types share a common identity concept. It is the most principled design and gives you real referential integrity. Denormalize `display_name` onto the supertype to avoid subtype joins for common queries (audit feeds, lists).

**Use Pattern 1** when moving fast or comfortable owning FK integrity in the application layer.

### Normalized vs Denormalized

**Recommended practice:** Start with a normalized schema (3NF), then selectively denormalize only the hotspots where joins are measurably slow. This hybrid approach gives you clean data with targeted performance boosts.

**When to normalize:** Transactional systems (banking, inventory, ERP) where accuracy, redundancy control, and storage efficiency matter most.

**When to denormalize:** Read-heavy workloads (data warehouses, dashboards, BI tools) where retrieval speed is the priority. Denormalization deliberately introduces redundancy to speed up certain queries at the cost of extra storage and increased risk of anomalies.

**SQLite-specific consideration:** Because SQLite is embedded (zero network latency), the N+1 problem is far less costly than with client/server databases. Multiple simple queries often outperform complex joins, so the pressure to denormalize is lower than in PostgreSQL or MySQL.

**Benchmark reference:** In one test with 5,000 bars and 10K wines, denormalized queries ran 16x faster for one pattern (569ms vs 9,143ms) and 104x faster for another (83ms vs 8,648ms). The denormalized database was 50% smaller.

Sources:
- [Database Schema Design Patterns for SQLite](https://sqleditor.online/blog/sqlite-schema-design-patterns)
- [Database Design Patterns Every Developer Should Know](https://www.bytebase.com/blog/database-design-patterns/)
- [ByteByteGo: Normalization vs Denormalization](https://blog.bytebytego.com/p/database-schema-design-simplified)
- [SQLite JSON and Denormalization](https://maximeblanc.fr/blog/sqlite-json-and-denormalization)

### JSON Columns

SQLite's JSON functions let you store structured data in TEXT columns while still querying into them.

**Core extraction:**

```sql
-- json_extract: returns SQL type for scalars, JSON text for objects/arrays
SELECT json_extract(data, '$.name') FROM events;
-- For {"name": "alice"} returns: 'alice'

-- ->> operator: always returns SQL type (TEXT, INTEGER, REAL, NULL)
SELECT data ->> '$.name' FROM events;

-- -> operator: always returns JSON text representation
SELECT data -> '$.tags' FROM events;
-- For {"tags": [1,2]} returns: '[1,2]'
```

**Iterating arrays with json_each:**

```sql
-- Find users with a 704 area code phone number
SELECT DISTINCT user.name
FROM user, json_each(user.phone)
WHERE json_each.value LIKE '704-%';
```

**Modifying JSON:**

```sql
-- json_set: creates or overwrites
UPDATE events SET data = json_set(data, '$.status', 'processed');

-- json_insert: creates only (won't overwrite)
UPDATE events SET data = json_insert(data, '$.new_field', 42);

-- json_replace: overwrites only (won't create)
UPDATE events SET data = json_replace(data, '$.status', 'done');

-- Append to array (use $[#] for end position)
UPDATE events SET data = json_set(data, '$.tags[#]', 'new-tag');

-- Remove a key
UPDATE events SET data = json_remove(data, '$.temp_field');
```

**Aggregating rows into JSON:**

```sql
-- Build a JSON array from rows
SELECT json_group_array(json_object('id', id, 'name', name)) FROM users;
-- Returns: [{"id":1,"name":"alice"}, {"id":2,"name":"bob"}]

-- Build a JSON object from rows
SELECT json_group_object(name, score) FROM leaderboard;
-- Returns: {"alice":100, "bob":85}
```

**Validation:**

```sql
SELECT json_valid('{"x":35}');     -- 1 (valid)
SELECT json_valid('{"x":35');      -- 0 (invalid)
SELECT json_valid('{x:35}', 6);   -- 1 (valid JSON5 or JSONB)
```

Source: [SQLite JSON Functions](https://sqlite.org/json1.html)

### Generated Columns for JSON Indexing

The most powerful pattern for JSON performance: virtual generated columns with B-tree indexes.

```sql
CREATE TABLE documents (
  id INTEGER PRIMARY KEY,
  body TEXT  -- JSON
);

-- Extract fields as virtual generated columns
ALTER TABLE documents ADD COLUMN doc_type TEXT
  GENERATED ALWAYS AS (body ->> '$.type') VIRTUAL;

ALTER TABLE documents ADD COLUMN author TEXT
  GENERATED ALWAYS AS (body ->> '$.author') VIRTUAL;

-- Index the generated columns for B-tree speed
CREATE INDEX idx_doc_type ON documents(doc_type);
CREATE INDEX idx_author ON documents(author);

-- Queries now use indexes (verify with EXPLAIN QUERY PLAN):
SELECT * FROM documents WHERE doc_type = 'report' AND author = 'alice';
-- SEARCH documents USING INDEX idx_doc_type (doc_type=?)
```

**VIRTUAL vs STORED:**
- VIRTUAL: computed on read, no disk space, can be added with ALTER TABLE
- STORED: computed on write, uses disk space, cannot be added with ALTER TABLE
- Use STORED when reads vastly outnumber writes; VIRTUAL otherwise

**Key advantages:**
- No extra write overhead (VIRTUAL columns are computed on read)
- Can be added with ALTER TABLE without rebuilding the table
- Indexes work exactly like regular column indexes
- Zero back-filling when adding new virtual columns

Sources: [SQLite Generated Columns](https://sqlite.org/gencol.html), [SQLite JSON Virtual Columns + Indexing](https://www.dbpro.app/blog/sqlite-json-virtual-columns-indexing)

### Materialized Views via Triggers

SQLite has no native materialized views. Simulate them with a table + triggers:

```sql
-- 1. Create the materialized view table
CREATE TABLE report_summary (
  report_id  INTEGER PRIMARY KEY,
  category   TEXT NOT NULL,
  item_count INTEGER NOT NULL DEFAULT 0,
  last_updated TEXT NOT NULL
);

-- 2. Populate on insert to source table
CREATE TRIGGER trg_report_insert AFTER INSERT ON items
BEGIN
  INSERT INTO report_summary (report_id, category, item_count, last_updated)
    VALUES (NEW.report_id, NEW.category, 1, datetime('now'))
    ON CONFLICT(report_id) DO UPDATE SET
      item_count = item_count + 1,
      last_updated = datetime('now');
END;

-- 3. Update on delete from source table
CREATE TRIGGER trg_report_delete AFTER DELETE ON items
BEGIN
  UPDATE report_summary
    SET item_count = item_count - 1,
        last_updated = datetime('now')
    WHERE report_id = OLD.report_id;
END;

-- 4. Full refresh when triggers are insufficient
DELETE FROM report_summary;
INSERT INTO report_summary (report_id, category, item_count, last_updated)
  SELECT report_id, category, COUNT(*), datetime('now')
  FROM items GROUP BY report_id, category;
```

**Tradeoffs:**
- Trigger-maintained: always current, adds overhead to every write on the source table
- Scheduled refresh: stale between refreshes, no write overhead
- Choose triggers for small-to-medium tables; scheduled refresh for large aggregation tables

Source: [SQLite Triggers as Materialized Views](https://madflex.de/SQLite-triggers-as-replacement-for-a-materialized-view/)

### EAV (Entity-Attribute-Value) Pattern

**What it is:** Three columns -- `entity_id`, `attribute_name`, `value` -- allowing flexible attributes per entity.

```sql
CREATE TABLE product_attributes (
    entity_id  INTEGER REFERENCES products(product_id),
    attribute  TEXT NOT NULL,
    value      TEXT,
    PRIMARY KEY (entity_id, attribute)
);
```

**When to use:** Product catalogs with hundreds of optional attributes, clinical records with thousands of possible fields, or any domain where the set of attributes is not known at schema design time.

**Why it often fails:**
- Every query retrieving multiple attributes requires self-joins or pivot operations
- Filtering is slow because `value` is always TEXT (no type enforcement)
- No foreign key constraints on values
- Query complexity grows multiplicatively with each attribute

**Modern alternative for SQLite:** Use typed columns for core fields and JSON for variable attributes (requires SQLite 3.38.0+ for `->>` operator):

```sql
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    price      REAL NOT NULL,
    attributes TEXT DEFAULT '{}'  -- JSON
);

-- Query with JSON:
SELECT product_id, name, attributes ->> '$.color' AS color
FROM products
WHERE attributes ->> '$.color' = 'red';

-- Index on JSON field:
CREATE INDEX ix_products_color ON products(attributes ->> '$.color');
```

Sources:
- [Database Design Patterns Every Developer Should Know](https://www.bytebase.com/blog/database-design-patterns/)
- [Universal Database Design Patterns](https://www.red-gate.com/blog/database-design-patterns/)

### Single-Table Inheritance

All subtypes stored in one table with a `type` discriminator column. Subtype-specific columns are NULL for rows of other types.

```sql
CREATE TABLE vehicles (
    vehicle_id    INTEGER PRIMARY KEY,
    vehicle_type  TEXT NOT NULL CHECK (vehicle_type IN ('car', 'truck', 'motorcycle')),
    make          TEXT NOT NULL,
    model         TEXT NOT NULL,
    -- car-specific
    num_doors     INTEGER,
    -- truck-specific
    payload_tons  REAL,
    -- motorcycle-specific
    engine_cc     INTEGER
);
```

**When to use:** Few subtypes (2-4), subtypes share most columns, and you query across all types frequently. Simple to implement, single-table scans, no joins needed.

**When to avoid:** Many subtypes, subtypes have few shared columns (table becomes mostly NULL), or you need strict NOT NULL constraints on subtype-specific fields.

**SQLite-specific consideration:** Without STRICT mode, SQLite will happily store any type in any column, so the CHECK constraint on `vehicle_type` is your main safety net. Consider STRICT tables (SQLite 3.37.0+) for type enforcement.

### Adjacency Lists and Tree Hierarchies

Three primary patterns for hierarchical data:

#### Adjacency List (simplest)

```sql
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    parent_id   INTEGER REFERENCES categories(category_id)
);
```

Simple to implement. Finding immediate children: `WHERE parent_id = ?`. Finding all descendants requires recursive CTEs (SQLite 3.8.3+):

```sql
WITH RECURSIVE descendants AS (
    SELECT category_id, name, parent_id FROM categories WHERE category_id = ?
    UNION ALL
    SELECT c.category_id, c.name, c.parent_id
    FROM categories c
    JOIN descendants d ON c.parent_id = d.category_id
)
SELECT * FROM descendants;
```

**Trade-offs:** Minimal storage, simple writes, but recursive reads.

#### Closure Table (best for read-heavy hierarchies)

```sql
CREATE TABLE category_closure (
    ancestor_id   INTEGER NOT NULL REFERENCES categories(category_id),
    descendant_id INTEGER NOT NULL REFERENCES categories(category_id),
    depth         INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (ancestor_id, descendant_id)
);
```

Every path in the hierarchy is stored as a row. Efficient queries without recursion:

```sql
-- All descendants of node 1:
SELECT descendant_id FROM category_closure WHERE ancestor_id = 1;

-- All ancestors of node 4:
SELECT ancestor_id FROM category_closure WHERE descendant_id = 4;

-- Direct children only:
SELECT descendant_id FROM category_closure WHERE ancestor_id = 1 AND depth = 1;
```

**Trade-offs:** Excellent read performance (indexed flat queries, no recursion), but O(n^2) worst-case storage and complex insert/delete maintenance.

**SQLite-specific:** SQLite has a `transitive_closure` extension that auto-maintains the closure table from an adjacency list.

#### Nested Sets (best for static hierarchies)

```sql
CREATE TABLE categories (
    category_id    INTEGER PRIMARY KEY,
    name           TEXT NOT NULL,
    left_boundary  INTEGER NOT NULL,
    right_boundary INTEGER NOT NULL
);

-- All descendants of node with left=1, right=10:
SELECT * FROM categories
WHERE left_boundary > 1 AND right_boundary < 10;
```

**Trade-offs:** Excellent read performance without recursion, low storage, but adding/deleting/moving nodes requires renumbering boundaries -- expensive for frequently-modified trees.

#### Decision Table

| Pattern | Read Performance | Write Complexity | Storage | Best For |
|---------|-----------------|-----------------|---------|----------|
| Adjacency List | Moderate (recursive) | Simple | Minimal | Dynamic trees with few depth queries |
| Closure Table | Excellent | Moderate | High | Read-heavy, deep hierarchies |
| Nested Sets | Excellent | High (renumbering) | Low | Static/rarely-modified hierarchies |

Sources:
- [Mastering SQL Trees: Adjacency Lists to Nested Sets and Closure Tables](https://teddysmith.io/sql-trees/)
- [Querying Tree Structures in SQLite](https://charlesleifer.com/blog/querying-tree-structures-in-sqlite-using-python-and-the-transitive-closure-extension/)
- [Hierarchical Data in SQL: The Ultimate Guide](https://www.databasestar.com/hierarchical-data-sql/)

---
