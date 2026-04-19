---

id: 607B9F71-39DD-4B10-80FD-D8FD115CCE5F
title: "Database backup and recovery"
domain: agentic-cookbook://guidelines/implementing/data/backup-and-recovery
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Prescriptive rules for SQLite backup methods, corruption prevention, integrity checking, recovery procedures, VACUUM strategy, and database size management."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - backup
  - recovery
  - operations
  - litestream
  - wal
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
references:
  - https://sqlite.org/backup.html
  - https://sqlite.org/howtocorrupt.html
  - https://sqlite.org/recovery.html
  - https://litestream.io/how-it-works/
  - https://sqlite.org/wal.html
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - configuration
---

# Database backup and recovery

## Backup methods

Choose the backup method that matches your durability requirements and operational constraints.

**`.backup` command** is the recommended default for most cases. It performs a page-by-page replica without locking the database for the duration — other connections can continue writing, though their changes will not appear in the backup.

```bash
sqlite3 mydb.db ".backup backup.db"
```

**`VACUUM INTO`** produces a compacted copy and is preferred when storage efficiency matters. It is more CPU-intensive than `.backup` but eliminates free-page waste and defragments the file.

```sql
VACUUM INTO '/path/to/backup.db';
```

**Online Backup API** (programmatic) copies pages incrementally, acquiring a read lock only during each step rather than the entire backup. Use this when you need progress monitoring or integration into application code.

```python
source = sqlite3.connect('mydb.db')
dest   = sqlite3.connect('backup.db')
source.backup(dest, pages=100)   # copies 100 pages per step
dest.close()
source.close()
```

**Litestream** MUST be used when you need continuous, point-in-time recovery for a production server-side SQLite database. It takes over WAL checkpointing, streams WAL pages to S3-compatible storage, and periodically snapshots the full database.

```yaml
dbs:
  - path: /path/to/app.db
    replicas:
      - type: s3
        bucket: my-backup-bucket
        path: app.db
        retention: 72h
```

Litestream is a disaster-recovery tool, not a sync tool. It replicates one database to one storage destination. Do not use it to synchronize multiple writers.

## WAL files during restore

When restoring a backup, you MUST delete any existing `*-wal` and `*-shm` files at the destination before copying the backup file. A stale or mismatched WAL file will corrupt the restored database. The WAL and database file are a matched pair — they cannot be mixed.

```bash
rm -f restored.db-wal restored.db-shm
cp backup.db restored.db
```

## Corruption prevention

SQLite is highly resistant to corruption. Crashed transactions are automatically rolled back on next access. Corruption almost always originates from one of these causes:

- **Network filesystems** — never run SQLite on NFS, CIFS, or any networked filesystem. File locking is unreliable.
- **Synchronous mode too low** — `PRAGMA synchronous = OFF` allows the OS to lie about writes completing. SHOULD use `NORMAL` (safe with WAL mode) or `FULL`.
- **Deleting journal files** — deleting `*-journal` or `*-wal` while the database is open prevents crash recovery.
- **Multiple processes writing directly** — only allow SQLite's own locking to coordinate access.
- **Moving a database without its journal** — the database and its journal/WAL are a unit.

These PRAGMAs MUST NOT be set in production:

```sql
PRAGMA synchronous = OFF;       -- risk of corruption on power loss
PRAGMA journal_mode = OFF;      -- disables crash recovery entirely
PRAGMA journal_mode = MEMORY;   -- same risk as OFF
```

## Integrity checking

Run integrity checks on a schedule or after any suspect event (disk errors, process kills, power loss).

```sql
PRAGMA integrity_check;   -- thorough; slow on large databases
PRAGMA quick_check;       -- faster, catches most problems
```

`integrity_check` returns `ok` on a healthy database. Any other output indicates damage. Schedule `quick_check` on startup for databases that are critical to the application. Reserve `integrity_check` for periodic offline audits.

## Recovery from corruption

SQLite 3.29.0+ includes a built-in recovery tool that extracts whatever data remains readable from a corrupted file.

```bash
sqlite3 corrupted.db ".recover" | sqlite3 recovered.db
```

For older versions, extract data manually:

```bash
sqlite3 corrupted.db ".mode insert" ".output dump.sql" ".dump" ".output stdout"
sqlite3 new.db < dump.sql
```

Recovery is always partial — some rows may be unrecoverable. The best recovery strategy is a recent backup.

## VACUUM strategy

Free pages accumulate as rows are deleted. SQLite does not return this space to the filesystem automatically.

**Prefer incremental VACUUM** for running applications. It reclaims a bounded number of pages per call without locking the database for long.

```sql
PRAGMA incremental_vacuum(500);  -- reclaim up to 500 pages
```

This requires `PRAGMA auto_vacuum = INCREMENTAL` set when the database was created.

**Full VACUUM** is appropriate after bulk deletes (25%+ of content removed) or offline maintenance windows. It rewrites the entire database and requires approximately 2x the database size in free disk space. It locks the database for its entire duration.

```sql
VACUUM;
```

SHOULD run VACUUM during application idle time (scheduled maintenance, app launch before first query). MUST NOT run VACUUM under high write load.

## Database size monitoring

Monitor database size so you can detect unexpected growth and decide when to VACUUM.

```sql
SELECT page_count * page_size AS total_bytes,
       freelist_count * page_size AS free_bytes
FROM pragma_page_count(), pragma_page_size(), pragma_freelist_count();
```

Alert when `free_bytes / total_bytes` exceeds 25% — that is a signal to VACUUM.

## Tombstone and outbox pruning

Soft-delete tombstones and sync outbox entries accumulate without a purge strategy. Define retention windows from the start.

```sql
-- Purge synced tombstones older than 90 days
DELETE FROM tasks_tombstones
WHERE synced = 1
  AND deleted_at < strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-90 days');

-- Purge completed outbox entries older than 7 days
DELETE FROM outbox
WHERE status = 'done'
  AND created_at < strftime('%Y-%m-%dT%H:%M:%fZ', 'now', '-7 days');
```

Only purge tombstones after confirming all sync targets have consumed them. Purging too early causes deleted records to reappear on devices that haven't synced yet.

After large purges, run `PRAGMA incremental_vacuum` to reclaim the freed pages.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
