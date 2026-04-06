---
title: "Operations and Maintenance"
domain: database
type: guideline
status: draft
created: 2026-04-03
modified: 2026-04-06
author: Mike Fullerton
summary: "Migration, backup/recovery, date handling, blob storage, security, testing, and common anti-patterns for SQLite"
platforms:
  - sqlite
tags:
  - database
  - sqlite
  - operations
references:
  - https://sqlite.org/backup.html
  - https://sqlite.org/lang_altertable.html
  - https://sqlite.org/intern-v-extern-blob.html
  - https://sqlite.org/datatype3.html
related:
  - schema-design.md
  - performance-and-tuning.md
---

# Operations and Maintenance

> Migration and versioning, backup and recovery, date handling, blob storage, security, testing, and common anti-patterns for SQLite.

---

## 13. Migration and Versioning

### Schema Versioning with PRAGMA user_version

Use SQLite's built-in `PRAGMA user_version` integer to track schema version. It is simpler and more efficient than maintaining a version table -- the integer is available immediately without searching the database file.

```sql
-- Read current version
PRAGMA user_version;

-- Set version after migration
PRAGMA user_version = 3;
```

**Migration file structure:**

```
migrations/
  0001_initial_schema.sql
  0002_add_indexes.sql
  0003_add_fts.sql
```

Each migration file ends with `PRAGMA user_version = N;`

**Python implementation:**

```python
current = db.execute('PRAGMA user_version').fetchone()[0]
for migration_file in sorted(migration_files):
    version = int(migration_file.split('_')[0])
    if version > current:
        db.executescript(open(migration_file).read())
```

**Shell script implementation:**

```bash
current_version=$(sqlite3 "$DB" "PRAGMA user_version;")
for migration in migrations/*.sql; do
    version=$(basename "$migration" | cut -d_ -f1 | sed 's/^0*//')
    if [ "$version" -gt "$current_version" ]; then
        sqlite3 "$DB" < "$migration"
    fi
done
```

**Best practices:**
- Keep migration SQL scripts in version control
- Wrap each migration in a transaction (BEGIN/COMMIT)
- Design scripts to be safely re-runnable (idempotent where possible)
- Number migrations sequentially to ensure ordering
- Include both the DDL changes and the `PRAGMA user_version = N` in each file

Sources:
- [SQLite DB Migrations with PRAGMA user_version](https://levlaz.org/sqlite-db-migrations-with-pragma-user_version/)
- [SQLite's user_version pragma for schema versioning](https://gluer.org/blog/sqlites-user_version-pragma-for-schema-versioning/)

### ALTER TABLE Limitations

SQLite's ALTER TABLE is severely limited. It supports:
- `ALTER TABLE x RENAME TO y`
- `ALTER TABLE x ADD COLUMN y` (column must have a default value or allow NULL)
- `ALTER TABLE x RENAME COLUMN old TO new` (SQLite 3.25.0+)
- `ALTER TABLE x DROP COLUMN y` (SQLite 3.35.0+)

It does **not** support changing column types, adding/removing constraints, changing default values, or reordering columns.

**The 12-step migration procedure** for structural changes:

```sql
-- Example: changing a column type and adding a constraint
BEGIN TRANSACTION;
PRAGMA foreign_keys = OFF;

CREATE TABLE items_new (
    item_id INTEGER PRIMARY KEY,
    name    TEXT NOT NULL,
    price   REAL NOT NULL CHECK (price >= 0)  -- was TEXT, now REAL with constraint
);

INSERT INTO items_new (item_id, name, price)
SELECT item_id, name, CAST(price AS REAL) FROM items;

DROP TABLE items;
ALTER TABLE items_new RENAME TO items;

PRAGMA foreign_key_check;  -- verify no broken references
PRAGMA foreign_keys = ON;
COMMIT;
```

**Critical:** The sequence (create new, copy, drop old, rename new) is important to avoid breaking foreign key references.

**Declarative migration approach:** Compare the actual database against a "pristine" in-memory database created from the schema definition. The migrator queries `sqlite_schema` to identify differences and applies changes automatically. Works well for adding new tables, modifying indexes, and adding nullable columns. Requires manual SQL for data migrations.

Sources:
- [Simple declarative schema migration for SQLite](https://david.rothlis.net/declarative-schema-migration-for-sqlite/)
- [SQLite ALTER TABLE documentation](https://sqlite.org/lang_altertable.html)

---

## 14. Backup and Recovery

### Backup Methods

#### .backup Command (built-in, recommended default)

```
sqlite3 mydb.db ".backup backup.db"
```

Creates a page-by-page replica. Other connections can write during the backup, but those changes will not appear in the backup.

#### VACUUM INTO (backup + optimize)

```sql
VACUUM INTO '/path/to/backup.db';
```

Creates a vacuumed (compacted) copy. More CPU-intensive than `.backup` but produces a smaller, defragmented file.

#### Online Backup API (programmatic, incremental)

The C API copies pages incrementally without locking the source for the entire duration:

- `sqlite3_backup_init()` -- creates backup object
- `sqlite3_backup_step(N)` -- copies N pages per iteration
- `sqlite3_backup_finish()` -- releases resources

The source is read-locked only while pages are being read. Progress monitored with `sqlite3_backup_remaining()` and `sqlite3_backup_pagecount()`.

#### Litestream (continuous replication to S3)

Streams WAL changes to S3-compatible storage. Provides point-in-time recovery. Requires additional software.

#### Copy-on-Write (filesystem-level)

On Btrfs/XFS, `cp --reflink=always` within a deferred transaction creates near-instant backups (~2ms for 440MB+).

### Comparison

| Method | Durability | Space | Restore Speed | Complexity |
|--------|-----------|-------|---------------|-----------|
| `.backup` | High | Moderate | Very Fast | Low |
| `VACUUM INTO` | High | Small (compacted) | Very Fast | Low |
| Online Backup API | High | Moderate | Very Fast | Medium |
| Litestream | Very High | Low (incremental) | Moderate | Medium |
| CoW `cp` | High | Very Low | Very Fast | Low |
| `.dump` (SQL) | High | Large | Slow | Low |

### Critical WAL Consideration

When restoring a backup, **always delete any existing `*-wal` and `*-shm` files** at the destination before copying. A stale/mismatched WAL file can corrupt the restored database.

### Corruption Prevention

SQLite is highly resistant to corruption -- partial transactions from crashes are automatically rolled back on next access. Corruption can occur from:

1. **Rogue process overwrites** -- other processes writing directly to the database file
2. **Broken file locking** -- especially on network filesystems (NFS, CIFS). Never use SQLite on network storage.
3. **Sync failures** -- disk drives reporting writes complete before reaching persistent media. Use `PRAGMA synchronous = FULL` (or `NORMAL` with WAL mode).
4. **Deleting journal files** -- removing `*-journal` or `*-wal` files prevents crash recovery
5. **Memory corruption** -- stray pointers, especially with memory-mapped I/O
6. **Mismatched database + journal** -- renaming or moving the database without its journal

**Integrity checking:**

```sql
PRAGMA integrity_check;       -- thorough check (slow on large DBs)
PRAGMA quick_check;           -- faster, less thorough
```

**Recovery from corruption:**

```sql
-- SQLite 3.29.0+
.recover
-- Or manually:
.mode insert
.output recovery.sql
.dump
.output stdout
```

**Configuration rules to prevent corruption:**
- Never use `PRAGMA synchronous = OFF`
- Never use `PRAGMA journal_mode = OFF` or `MEMORY`
- Never modify `PRAGMA schema_version` with active connections
- Use `PRAGMA writable_schema = ON` with extreme caution

Sources:
- [SQLite Backup API](https://sqlite.org/backup.html)
- [How To Corrupt An SQLite Database File](https://sqlite.org/howtocorrupt.html)
- [Recovering Data From A Corrupt SQLite Database](https://sqlite.org/recovery.html)
- [Backup strategies for SQLite in production](https://oldmoe.blog/2024/04/30/backup-strategies-for-sqlite-in-production/)

---

## 15. Date and Time Handling

### Storage Format Options

SQLite has no native datetime type. Three storage approaches:

#### TEXT -- ISO-8601 strings (recommended default)

```sql
CREATE TABLE events (
    event_id   INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
-- Stores: '2026-04-03 14:30:00'
```

**Pros:** Human-readable, built-in function support (`datetime()`, `date()`, `time()`), supports timezone info, millisecond precision.
**Cons:** 20-27 bytes per timestamp (vs 8 for INTEGER), string comparison slightly slower.

#### INTEGER -- Unix timestamps

```sql
CREATE TABLE events (
    event_id   INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (unixepoch('now'))
);
-- Stores: 1775403000
```

**Pros:** 8 bytes, fastest comparisons, simplest arithmetic, timezone-neutral (always UTC), efficient range queries.
**Cons:** Not human-readable, requires conversion for display. **Caution:** Timestamps from the first 63 days of 1970 may be misinterpreted as Julian day numbers by the `auto` modifier.

#### REAL -- Julian day numbers

```sql
SELECT julianday('now');  -- 2460737.10417
```

**Pros:** Most precise for day-based calculations.
**Cons:** Rarely used, unfamiliar to most developers.

### Core Date Functions

```sql
-- Current UTC timestamp
SELECT datetime('now');                          -- '2026-04-03 14:30:00'
SELECT unixepoch('now');                         -- 1775403000

-- Convert between formats
SELECT datetime(1775403000, 'unixepoch');        -- INTEGER to TEXT
SELECT strftime('%s', '2026-04-03 14:30:00');    -- TEXT to INTEGER

-- Date arithmetic
SELECT datetime('now', '+7 days');               -- 7 days from now
SELECT datetime('now', '-1 month');              -- 1 month ago
SELECT date('now', 'start of month', '+1 month', '-1 day');  -- end of current month

-- Day-based calculations
SELECT julianday('now') - julianday('2026-01-01') AS days_elapsed;

-- Validation (returns NULL for invalid dates)
SELECT datetime('2026-13-45');  -- NULL
```

### Critical Best Practices

**Always store UTC.** Converting to local time is a display concern:

```sql
-- Store in UTC
INSERT INTO events (name, created_at) VALUES ('test', datetime('now'));

-- Display in local time
SELECT datetime(created_at, 'localtime') AS local_time FROM events;
```

**Never mix formats in the same column.** Pick TEXT or INTEGER and use it consistently. Mixed formats break comparisons and indexing.

**Be consistent with precision.** If you store milliseconds in some rows and seconds in others, comparisons break.

**Month arithmetic can surprise:**

```sql
SELECT date('2026-01-31', '+1 month');  -- result may vary
```

### Choosing a Format

| Criterion | TEXT (ISO-8601) | INTEGER (Unix) |
|-----------|----------------|----------------|
| Human readability | Excellent | Poor |
| Storage size | 20-27 bytes | 8 bytes |
| Comparison speed | Good | Best |
| Date arithmetic | Via functions | Simple addition |
| Range queries | Good | Best |
| Timezone clarity | Can include offset | Always UTC |
| Function support | Native | Requires 'unixepoch' modifier |

**For most applications:** TEXT ISO-8601 is the safer default -- easier to debug and works naturally with SQLite's date functions.

**For high-volume logging or time-series data:** INTEGER unix timestamps for storage efficiency and comparison speed.

Sources:
- [Handling Timestamps in SQLite](https://blog.sqlite.ai/handling-timestamps-in-sqlite)
- [SQLite Date & Time Functions](https://sqlite.org/lang_datefunc.html)
- [SQLite Date & Time Tutorial](https://www.sqlitetutorial.net/sqlite-date/)

---

## 16. Blob and Large Data

### The 100KB Threshold

SQLite's own benchmarks established a clear guideline:

- **Under 100KB:** Reading BLOBs from the database is **faster** than from separate files. At 10KB, SQLite is 35% faster than filesystem I/O and uses 20% less disk space.
- **Over 100KB:** Reading from separate files is faster. The crossover varies by hardware (between 100KB and 1MB depending on page size).

### When to Store BLOBs in the Database

**Do store internally:**
- Small files under 100KB (thumbnails, icons, small config files)
- When ACID guarantees on the data matter
- When atomic updates of both metadata and content are needed

**Store externally (file path in DB):**
- Files over 100KB (videos, PDFs, large images)
- When files are served directly via a web server
- When files are accessed independently of their metadata

**Hybrid approach:** Store small BLOBs internally, large BLOBs externally with the path in the database.

### Page Size Optimization

```sql
-- Set before creating the database (cannot change after)
PRAGMA page_size = 8192;   -- or 16384 for large BLOB I/O
```

A page size of 8192 or 16384 gives the best performance for large BLOB I/O. The default 4096 is fine for non-BLOB workloads.

### Maximum BLOB Size

- Default maximum: 1,000,000,000 bytes (1 GB)
- Absolute maximum: 2,147,483,647 bytes (~2 GB)
- Configurable via `SQLITE_MAX_LENGTH` compile-time option

### ZEROBLOB for Incremental Writing

`zeroblob()` allocates space filled with zeros, then you overwrite in chunks via the blob I/O API:

```sql
INSERT INTO files (name, content) VALUES ('large.bin', zeroblob(1048576));
-- Then use sqlite3_blob_open() / sqlite3_blob_write() to write in chunks
```

This avoids loading the entire BLOB into memory at once.

### ACID vs Performance Trade-off

Storing files in the database gives you ACID properties (atomic updates, crash recovery). External files lose ACID but gain direct filesystem access, CDN compatibility, no database size bloat, and independent backup.

Sources:
- [Internal Versus External BLOBs](https://sqlite.org/intern-v-extern-blob.html)
- [35% Faster Than The Filesystem](https://sqlite.org/fasterthanfs.html)
- [Implementation Limits For SQLite](https://sqlite.org/limits.html)

---

## 17. Security

### SQL Injection Prevention

**The rule:** Use prepared statements with bind parameters. Do not try to play games attempting to outthink your attacker. Prepared statements separate SQL code from data -- the database engine treats bound parameters as data, never as executable code.

**In Python:**

```python
# DANGEROUS -- string concatenation
cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")

# SAFE -- parameterized query
cursor.execute("SELECT * FROM users WHERE name = ?", (user_input,))
```

**In shell scripts:** The `sqlite3` CLI does not natively support parameterized queries. This is the biggest security risk for shell script database access.

**Option 1 -- .parameter bind (sqlite3 3.38.0+):**

```bash
sqlite3 "$DB" <<EOF
.parameter set :name '$sanitized_name'
SELECT * FROM users WHERE name = :name;
EOF
```

**Option 2 -- Validate and escape in the shell script:**

```bash
# Minimal escaping: double all single quotes
safe_input="${user_input//\'/\'\'}"
sqlite3 "$DB" "SELECT * FROM users WHERE name = '${safe_input}'"
```

This is inferior to prepared statements but may be the only option in pure shell.

**Option 3 -- Delegate to a helper program:**

Write a small Python/Go/Rust wrapper that accepts arguments and uses proper parameterized queries. The shell script calls the wrapper. This is the most secure approach for shell-based architectures.

**Option 4 -- sqlite3_mprintf format specifiers (`%q`, `%Q`, `%w`):**

In C code, `%q` doubles single quotes, `%Q` wraps in quotes and handles NULL, `%w` is for identifiers.

### Database File Permissions

SQLite delegates all access control to the operating system. It does not implement GRANT/REVOKE or user authentication.

```bash
# Database file: owner read/write only
chmod 600 mydb.db

# Set umask before creating databases
umask 077
sqlite3 newdb.db "CREATE TABLE test (id INTEGER PRIMARY KEY);"
```

**Important considerations:**
- The database file, WAL file, and journal file must all have consistent permissions
- The directory containing the database must be writable (SQLite creates temporary files)
- On WAL mode, read-only connections still need write permission to the WAL and SHM files
- Never make database files world-readable if they contain sensitive data

### Additional Security Measures

- **Principle of least privilege:** Run database-accessing processes under a restricted user account
- **Encryption at rest:** SQLite has no built-in encryption. Use SQLCipher or SEE (SQLite Encryption Extension) for encrypted databases
- **Input validation:** Beyond SQL injection, validate that inputs conform to expected formats before they reach the query layer
- **LIKE clause escaping:** User input in LIKE patterns needs the ESCAPE clause:

```sql
SELECT * FROM items WHERE name LIKE '%' || :search || '%' ESCAPE '\';
```

Sources:
- [SQLite Forum: Characters to escape to prevent SQL Injection](https://sqlite.org/forum/info/53ec3a55cb9fc1d3)
- [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [Basic Security Practices for SQLite](https://dev.to/stephenc222/basic-security-practices-for-sqlite-safeguarding-your-data-23lh)

---

## 18. Testing with SQLite

### In-Memory Databases

The foundation of SQLite testing is `:memory:`, which creates a RAM-only database destroyed when the connection closes.

```python
import sqlite3
conn = sqlite3.connect(':memory:')
conn.executescript(open('schema.sql').read())
# ... run tests ...
conn.close()  # database destroyed
```

**Key advantages:** Speed (no disk I/O), isolation (each connection independent), simplicity (no files to manage), reproducibility (known blank state).

### Test Isolation Strategies

#### Strategy 1 -- Fresh Database Per Test (strongest isolation)

```python
import pytest, sqlite3

@pytest.fixture
def db():
    conn = sqlite3.connect(':memory:')
    conn.executescript(open('schema.sql').read())
    yield conn
    conn.close()

def test_insert_user(db):
    db.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
    assert db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1

def test_empty_users(db):
    # Guaranteed empty -- no cross-test contamination
    assert db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
```

**Pros:** Perfect isolation, simple to reason about.
**Cons:** Schema setup cost per test (usually negligible).

#### Strategy 2 -- Transaction Rollback (faster for large schemas)

```python
@pytest.fixture
def db(shared_db):
    shared_db.execute("BEGIN")
    yield shared_db
    shared_db.execute("ROLLBACK")
```

Schema created once. Tests must not COMMIT; nested transactions need SAVEPOINTs.

#### Strategy 3 -- Template Database with Backup API

```python
@pytest.fixture(scope='session')
def template_db():
    conn = sqlite3.connect(':memory:')
    conn.executescript(open('schema.sql').read())
    conn.executescript(open('test_seeds.sql').read())
    return conn

@pytest.fixture
def db(template_db):
    conn = sqlite3.connect(':memory:')
    template_db.backup(conn)
    return conn
```

Combines pre-populated data with per-test isolation using SQLite's backup API.

### Migration Testing

```python
def test_migrations_apply_cleanly():
    conn = sqlite3.connect(':memory:')
    for migration_file in sorted(glob.glob('migrations/*.sql')):
        conn.executescript(open(migration_file).read())
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    assert ('users',) in tables

def test_migration_idempotency():
    conn = sqlite3.connect(':memory:')
    for _ in range(2):
        for migration_file in sorted(glob.glob('migrations/*.sql')):
            conn.executescript(open(migration_file).read())
```

### Cross-Database Compatibility Caveats

When SQLite substitutes for a production database in tests:

| Behavior | SQLite | PostgreSQL | MySQL |
|----------|--------|------------|-------|
| String comparison | Case-sensitive | Case-sensitive (default) | Case-insensitive |
| Type enforcement | Flexible (unless STRICT) | Strict | Strict |
| Boolean type | INTEGER 0/1 | Native BOOLEAN | TINYINT |
| LIKE | Case-sensitive for ASCII | Case-insensitive (ILIKE) | Case-insensitive |

Test against the actual production database for integration tests. Use SQLite only for unit tests where dialect differences do not matter.

### Test Performance Tips

- Use function-scoped fixtures (one database per test) for isolation
- Use module/session-scoped fixtures for performance if tests are read-only
- Use `PRAGMA journal_mode = OFF` and `PRAGMA synchronous = OFF` in test databases for maximum speed (safe because test data is disposable)
- Pre-populate fixtures with representative data rather than building it per-test

Sources:
- [How to Use SQLite in Testing](https://oneuptime.com/blog/post/2026-02-02-sqlite-testing/view)
- [How SQLite Is Tested](https://sqlite.org/testing.html)
- [How to test SQLite in-memory databases using pytest](https://woteq.com/how-to-test-sqlite-in-memory-databases-using-pytest/)

---

## 19. Common Anti-Patterns

### Storing CSV/Lists in Columns

```sql
-- ANTI-PATTERN:
CREATE TABLE posts (
    post_id INTEGER PRIMARY KEY,
    tags    TEXT  -- 'python,sqlite,database'
);
```

Cannot index individual values, cannot join, cannot enforce referential integrity, requires LIKE '%tag%' (full table scan with false positives).

**Fix -- junction table:**

```sql
CREATE TABLE tags (
    tag_id INTEGER PRIMARY KEY,
    name   TEXT NOT NULL UNIQUE
);

CREATE TABLE post_tags (
    post_id INTEGER REFERENCES posts(post_id),
    tag_id  INTEGER REFERENCES tags(tag_id),
    PRIMARY KEY (post_id, tag_id)
);
```

Or for simpler cases, use JSON:

```sql
CREATE TABLE posts (
    post_id INTEGER PRIMARY KEY,
    tags    TEXT DEFAULT '[]'  -- JSON array
);

SELECT * FROM posts, json_each(posts.tags)
WHERE json_each.value = 'python';
```

### Not Using Transactions for Batch Operations

```sql
-- ANTI-PATTERN: each statement is an implicit transaction with fsync
INSERT INTO data VALUES (1, 'a');
INSERT INTO data VALUES (2, 'b');
-- ... 10,000 more

-- FIX: explicit transaction (2-20x faster)
BEGIN TRANSACTION;
INSERT INTO data VALUES (1, 'a');
INSERT INTO data VALUES (2, 'b');
-- ... 10,000 more
COMMIT;
```

The filesystem sync happens once at COMMIT instead of per-statement. Even read performance improves (fewer lock operations).

### Ignoring EXPLAIN QUERY PLAN

```sql
-- Always check query execution:
EXPLAIN QUERY PLAN SELECT * FROM users WHERE email = 'test@example.com';
-- SCAN users              <-- full table scan! needs an index
-- SEARCH users USING INDEX idx_email (email=?)  <-- good
```

Adopt a repeatable workflow: capture the query, EXPLAIN it, test with the fix, deploy.

### Using SQLite as a Message Queue

SQLite allows only one writer at a time. Queue patterns require frequent writes (enqueue) and deletes (dequeue) from competing processes, creating lock contention. Use a purpose-built queue instead.

**Exception:** A single-process queue (one producer, one consumer in the same application) works fine because there is no write contention.

### SELECT * in Production

Returns unnecessary columns, prevents index-only scans, breaks when schema changes, wastes memory. List only the columns you need.

### Functions on Indexed Columns

```sql
-- ANTI-PATTERN: cannot use index
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';

-- FIX: expression index (SQLite 3.9.0+)
CREATE INDEX ix_users_email_lower ON users(LOWER(email));
```

### N+1 Query Pattern

```sql
-- ANTI-PATTERN:
SELECT customer_id FROM customers;
-- Then for each: SELECT COUNT(*) FROM orders WHERE customer_id = ?;

-- FIX:
SELECT c.customer_id, c.name, COUNT(o.order_id) AS order_count
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name;
```

**SQLite caveat:** Because SQLite is embedded (no network hop), the N+1 penalty is smaller than with client/server databases. Sometimes N+1 with simple indexed lookups is actually faster than a complex join. Benchmark both.

### Long Transactions

In SQLite, an open write transaction blocks all other writers. A transaction held for 30 seconds blocks all writes for 30 seconds. Keep transactions short. Use `PRAGMA busy_timeout` for transient contention:

```sql
PRAGMA busy_timeout = 5000;  -- wait up to 5 seconds for locks
```

### SQLite vs Other Databases

#### What SQLite Excels At

SQLite "competes with `fopen()`" -- it is an embedded database engine, not a client/server system.

**Zero administration:** No server to install, configure, monitor, or restart. The database is a single file.

**Zero latency:** No network round-trip. Queries execute in-process.

**Ideal use cases:**
- **Application file format:** Desktop apps, mobile apps, Electron apps
- **Embedded/IoT devices:** Cellphones, cameras, drones, medical devices
- **Websites with < 100K hits/day**
- **Data analysis:** Import CSV/JSON, query with SQL, share the single file
- **Local caching and temporary databases**
- **Data transfer format:** Richer than CSV, simpler than a server

#### Where SQLite Falls Short

- **Write concurrency:** Unlimited readers but only one writer at a time
- **Network access:** Cannot connect from a different machine
- **Very large datasets:** Performance degrades above a few GB without careful tuning
- **Advanced SQL features:** No RIGHT JOIN, no FULL OUTER JOIN, limited ALTER TABLE, no stored procedures
- **Enterprise features:** No replication, no role-based access control, no audit logging

#### Decision Checklist

| Question | If Yes |
|----------|--------|
| Data on a separate server from the app? | Use client/server |
| Many concurrent writers needed? | Use client/server |
| Data exceeds a few GB? | Consider client/server |
| Multiple application servers sharing data? | Use client/server |
| Need user authentication at DB level? | Use client/server |
| Otherwise? | SQLite is likely the best choice |

#### Modern Performance Reality (2025-2026)

Recent benchmarks challenge traditional assumptions:
- A Rails app with 10 Puma workers achieved **2,730 write requests/second** using SQLite
- This supports ~1 million daily active users performing 35 writes/day each
- Key insight: match database connections to application workers, not excessive connection pools
- WAL mode with `busy_timeout` eliminates most "database locked" errors

#### Migration Away from SQLite

When migrating to PostgreSQL/MySQL:
- Tools like `sqlite3-to-mysql` handle encoding, type conversion, and bulk transfer
- SQLite's flexible typing may have allowed data that stricter databases reject -- validate data types first
- Date formats may need conversion (SQLite TEXT dates to native TIMESTAMP types)
- NULL handling differences may surface

Sources:
- [SQL Anti-Patterns and How to Fix Them](https://slicker.me/sql/antipatterns.htm)
- [SQLite Optimizations For Ultra High-Performance](https://www.powersync.com/blog/sqlite-optimizations-for-ultra-high-performance)
- [Database Design Patterns Every Developer Should Know](https://www.bytebase.com/blog/database-design-patterns/)
- [Appropriate Uses For SQLite](https://sqlite.org/whentouse.html)
- [Why you should probably be using SQLite](https://www.epicweb.dev/why-you-should-probably-be-using-sqlite)
- [SQLite vs MySQL vs PostgreSQL](https://www.digitalocean.com/community/tutorials/sqlite-vs-mysql-vs-postgresql-a-comparison-of-relational-database-management-systems)

---

