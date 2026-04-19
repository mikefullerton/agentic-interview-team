---

id: DB63C086-D082-4E20-AACA-154448C42D1D
title: "SQLite Sync Tooling"
domain: agentic-cookbook://guidelines/implementing/data/sync-tooling
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Comparison and selection guide for SQLite sync tools: Session Extension, cr-sqlite, Litestream, ElectricSQL, PowerSync, Turso/libSQL, and sqlite-sync — with a decision matrix and selection criteria."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - sync
  - tooling
  - sqlite
  - crdt
  - offline-first
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
  - guidelines/data/sync-engine-design.md
  - guidelines/data/conflict-resolution.md
references:
  - https://sqlite.org/sessionintro.html
  - https://github.com/vlcn-io/cr-sqlite
  - https://litestream.io
  - https://electric-sql.com
  - https://www.powersync.com
  - https://turso.tech
  - https://github.com/sqliteai/sqlite-sync
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - offline-support
  - dependency-management
---

# SQLite Sync Tooling

These tools address different parts of the sync problem. No single tool is universally correct — choose based on your write path requirements, server database, conflict resolution needs, and maturity tolerance.

## SQLite Session Extension

Built into SQLite (compile with `-DSQLITE_ENABLE_SESSION -DSQLITE_ENABLE_PREUPDATE_HOOK`). Records changes to attached tables and packages them as binary changesets.

**Capabilities:**
- Captures INSERT, UPDATE, DELETE as binary blobs with full before/after values
- Changesets can be applied to any other SQLite database with the same schema
- Built-in conflict handler callback with four conflict types (DATA, NOTFOUND, CONFLICT, CONSTRAINT)
- Supports changeset inversion (undo) and concatenation (batch multiple sessions)

**Limitations:** Tables must have a declared PRIMARY KEY. Virtual tables not supported. NULL values in PK columns are ignored. Requires C API — no official higher-level language bindings.

**Use when:** Syncing SQLite to SQLite (e.g., device-to-device or device-to-server SQLite), when you need full control over conflict handling, or when you're building a custom sync protocol on top of raw changesets.

## cr-sqlite

A loadable extension that adds multi-master replication via column-level CRDTs. Any table can become a conflict-free replicated relation (CRR) with one SQL call.

```sql
.load crsqlite
CREATE TABLE tasks (id TEXT PRIMARY KEY NOT NULL, title TEXT, status TEXT);
SELECT crsql_as_crr('tasks');

-- Export changes for sync
SELECT * FROM crsql_changes WHERE db_version > ?;

-- Import changes from another device
INSERT INTO crsql_changes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
```

**Conflict resolution:** Automatic LWW per column. Concurrent edits to different columns on the same row merge automatically. Only same-column conflicts require LWW fallback.

**Performance:** Writes approximately 2.5x slower than standard SQLite. Reads are identical.

**Limitations:** Beta maturity. No custom write-path business logic — CRDTs converge automatically, which means the server cannot reject writes. Schema changes require `crsql_begin_alter` / `crsql_commit_alter` wrappers.

**Use when:** Peer-to-peer sync, collaborative editing without a central server, or when you want automatic conflict resolution without custom code.

## Litestream

Streaming WAL-based replication for disaster recovery. NOT a multi-device sync tool.

Litestream takes over SQLite's WAL checkpointing, continuously streams new WAL pages to cloud storage (S3, Azure Blob, SFTP, GCS), and can create read replicas on other servers.

**Use when:** You need server-side SQLite backup, point-in-time recovery, or read replicas for a single-writer SQLite deployment. Do not use for device-to-server sync or multi-writer scenarios.

## ElectricSQL

Syncs PostgreSQL with client-side SQLite using Postgres logical replication (WAL streaming).

**Architecture:** An Electric service reads the Postgres WAL and streams changes to client-side SQLite (browser via WASM, mobile via native SQLite). Client writes go through Electric back to Postgres. Conflict resolution uses CRDTs (LWW semantics per field).

**Key characteristic:** "Direct-to-Postgres" — writes bypass your application backend. Validation happens via Postgres constraints and DDLX rules only.

**Trade-offs:**
- Pro: No backend code needed for sync
- Con: Cannot inject custom business logic on the write path
- Con: Requires SUPERUSER database privileges; modifies Postgres schema with shadow tables and triggers

**Use when:** The write path needs no custom logic, and you can accept Postgres-only as the server database.

## PowerSync

Postgres-to-SQLite sync engine with a server-authoritative write path.

**Architecture:** PowerSync Service connects to Postgres via logical replication (read-only) and streams data to client SQLite based on configurable Sync Rules. Client writes queue locally, then go through your own backend — your backend applies business logic, validation, and authorization before committing to Postgres. Changes committed to Postgres flow back to all clients via PowerSync.

**Key differentiator:** You control the write path. The server can reject, transform, or merge client writes with custom logic.

**Sync Rules** enable dynamic partial replication (e.g., sync only tasks belonging to the current user):

```yaml
- table: tasks
  filter: "user_id = token_parameters.user_id"
```

**Supported backends:** PostgreSQL (GA), MongoDB (GA).

**Use when:** You need server-authoritative writes with custom business logic, per-user data partitioning, and production-grade reliability.

## Turso / libSQL

A fork of SQLite with built-in replication and embedded replicas. The remote Turso database is the source of truth; each device holds a local SQLite copy for zero-latency reads.

Sync uses frame-based WAL replication. Supports manual sync (`client.sync()`), periodic polling (`syncInterval`), and offline writes pushed on reconnection.

**Conflict resolution options:**
- `DISCARD_LOCAL` — server-wins
- `REBASE_LOCAL` — replay local changes on top of server state
- `FAIL_ON_CONFLICT` — reject and surface to application
- `MANUAL_RESOLUTION` — callback with both versions

**Limitations:** Offline write sync is Beta maturity. Requires Turso Cloud as the server; not compatible with arbitrary Postgres backends.

**Use when:** You want embedded SQLite replicas with managed server infrastructure and are comfortable with Turso Cloud as your backend.

## sqlite-sync (sqlite.ai)

A CRDT-based loadable extension that syncs SQLite with SQLite Cloud, PostgreSQL, and Supabase.

```sql
.load cloudsync
SELECT cloudsync_init('tasks');
INSERT INTO tasks (id, title) VALUES (cloudsync_uuid(), 'New task');
SELECT cloudsync_network_init('your-database-id');
SELECT cloudsync_network_set_apikey('your-api-key');
SELECT cloudsync_network_sync();
```

Supports multiple CRDT algorithms per table: `cls` (Causal-Length Set, default), `dws` (Delete-Wins), `aws` (Add-Wins), `gos` (Grow-Only). Text columns support block-level LWW for per-line conflict resolution.

**Schema requirements:** All NOT NULL columns must have DEFAULT values. TEXT primary keys with UUIDv7 required. ALTER TABLE requires wrapping with `cloudsync_begin_alter` / `cloudsync_commit_alter`.

**Use when:** You want automatic CRDT-based sync with minimal code against SQLite Cloud, Postgres, or Supabase, and can accept Beta maturity.

## Tool Comparison Matrix

| Feature | Session Extension | cr-sqlite | Litestream | ElectricSQL | PowerSync | Turso | sqlite-sync |
|---------|:-----------------:|:---------:|:----------:|:-----------:|:---------:|:-----:|:-----------:|
| Sync direction | Manual | Bidirectional | One-way (backup) | Bidirectional | Bidirectional | Bidirectional | Bidirectional |
| Conflict resolution | Callback (custom) | CRDT automatic | N/A | CRDT (LWW) | Custom (your backend) | Multiple strategies | CRDT automatic |
| Server database | Any | Any | N/A (storage) | Postgres only | Postgres, MongoDB | Turso Cloud | SQLite Cloud, PG, Supabase |
| Offline writes | Yes | Yes | No | Yes | Yes | Yes (Beta) | Yes |
| Custom write logic | Yes | No | N/A | No | Yes | Partial | No |
| Setup complexity | Low (C API) | Low (extension) | Low (config file) | Medium | Medium | Low | Low (extension) |
| Maturity | Stable | Beta | Stable | Production | Production | Beta (offline) | Beta |

## Selection Criteria

1. **Do you need custom write-path business logic?** If yes: Session Extension (roll your own) or PowerSync. If no: cr-sqlite, ElectricSQL, sqlite-sync, or Turso.

2. **What is your server database?** Postgres only: ElectricSQL or PowerSync. Turso Cloud: Turso. SQLite Cloud or Supabase: sqlite-sync. Anything: Session Extension or cr-sqlite.

3. **Do you need production maturity?** Choose Session Extension, Litestream (for backup), ElectricSQL, or PowerSync. Avoid cr-sqlite, sqlite-sync, and Turso offline writes in production-critical systems.

4. **Is this backup/DR or active sync?** Backup only: Litestream. Active multi-device sync: everything else.

5. **Do you need peer-to-peer (no central server)?** cr-sqlite is the strongest choice. Session Extension with manual changeset exchange also works.

MUST evaluate maturity and support model before committing to a Beta tool in production. Prefer the Session Extension or PowerSync for production systems where stability and custom logic are priorities.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
