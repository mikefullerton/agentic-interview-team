---

id: 822A0912-FDA7-461F-85AB-F9C2C55F0039
title: "Conflict Resolution"
domain: agentic-cookbook://guidelines/implementing/data/conflict-resolution
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "How to choose and implement a conflict resolution strategy for sync: LWW, server-wins, field-level merge, CRDTs, Operational Transformation, and manual conflict queues."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - sync
  - conflict-resolution
  - crdt
  - offline-first
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
  - guidelines/data/sync-schema-design.md
  - guidelines/data/clock-systems.md
references:
  - https://crdt.tech/implementations
  - https://thom.ee/blog/crdt-vs-operational-transformation/
  - https://github.com/vlcn-io/cr-sqlite
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - offline-support
  - database-operations
---

# Conflict Resolution

A conflict occurs when the same record is modified on two devices (or by two users) between sync cycles. Every sync system MUST have an explicit conflict resolution strategy. "No strategy" means silent data loss.

## Choose a Strategy Per Data Type

No single strategy fits all data. Apply the simplest strategy that is correct for each entity type:

| Strategy | When to Use |
|----------|-------------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Last-Write-Wins (LWW) | Settings, preferences, low-contention single-user records |
| Server-wins | Admin-pushed config, read-only replication |
| Client-wins | Personal notes, drafts owned by one user |
| Field-level merge | Task trackers, CRMs — concurrent users edit different fields |
| CRDTs | Collaborative editing, peer-to-peer, extended offline periods |
| Operational Transformation | Collaborative text with a central server |
| Conflict queue | Medical, legal, financial — silent loss is unacceptable |

## Last-Write-Wins (LWW)

The most recent modification wins. Implement on the server with an UPSERT that compares timestamps or version numbers:

```sql
INSERT INTO tasks (id, title, status, updated_at, version)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT (id) DO UPDATE SET
    title      = EXCLUDED.title,
    status     = EXCLUDED.status,
    updated_at = EXCLUDED.updated_at,
    version    = EXCLUDED.version
WHERE EXCLUDED.updated_at > tasks.updated_at;
```

SHOULD use Hybrid Logical Clock (HLC) timestamps rather than wall-clock time to avoid clock-skew errors. Physical clocks on different devices can diverge by seconds or more, causing the wrong write to win.

MUST NOT use LWW for collaborative editing, financial records, or inventory — silent overwrites are destructive in those domains.

## Server-Wins vs Client-Wins

**Server-wins:** Discard the client's change when the server version is newer or equal. Safe for admin-pushed configuration and read-only sync scenarios.

**Client-wins:** Always apply the client's change. Equivalent to LWW where the client always has the "later" timestamp. Appropriate for personal data owned exclusively by one user.

Turso/libSQL exposes these as explicit strategies: `DISCARD_LOCAL` (server-wins), `REBASE_LOCAL` (replay client changes on top of server state), and `FAIL_ON_CONFLICT` (reject and surface to the application).

## Field-Level Merge (Three-Way Merge)

Instead of replacing the whole row, merge at the column level. If Device A changes `title` and Device B changes `status`, both edits survive.

Requires storing the **base version** — the last-synced state — for three-way comparison:

```python
def field_level_merge(client, server, base):
    merged = {}
    for field in all_fields:
        client_changed = client[field] != base[field]
        server_changed = server[field] != base[field]
        if client_changed and not server_changed:
            merged[field] = client[field]
        elif server_changed and not client_changed:
            merged[field] = server[field]
        elif client_changed and server_changed:
            if client[field] == server[field]:
                merged[field] = client[field]   # both agree
            else:
                merged[field] = resolve_field_conflict(field, client, server)
        else:
            merged[field] = base[field]
    return merged
```

MUST identify fields that form semantic groups and resolve them atomically — for example, `quantity` and `unit_price` should not be independently merged if `total` depends on both.

cr-sqlite implements per-column CRDTs that achieve field-level merge automatically, falling back to LWW only when the same field is concurrently modified.

## CRDTs (Conflict-Free Replicated Data Types)

CRDTs are data structures that converge automatically across replicas with no coordination required. Use them when devices may be offline for extended periods or when there is no reliable central server.

CRDT types for sync:

| Type | Behavior | Use Case |
|------|----------|----------|
| LWW-Register | Last write wins per field | Individual record fields |
| G-Counter | Grow-only counter | Page views, like counts |
| PN-Counter | Increment and decrement | Inventory, resource pools |
| OR-Set | Add/remove with add-wins | Shopping carts, tag sets |
| RGA | Replicated Growable Array | Collaborative text, ordered lists |

With cr-sqlite, mark a table as a conflict-free replicated relation (CRR) and normal SQL operations sync automatically:

```sql
.load crsqlite
CREATE TABLE tasks (id TEXT PRIMARY KEY NOT NULL, title TEXT, status TEXT);
SELECT crsql_as_crr('tasks');

-- Export changes for sync
SELECT * FROM crsql_changes WHERE db_version > ?;

-- Import changes from another device
INSERT INTO crsql_changes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
```

SHOULD NOT use CRDTs when business-logic validation must happen before a write is accepted — CRDTs converge by definition and cannot reject writes after the fact.

## Operational Transformation (OT)

OT transforms concurrent operations so they can be applied in any order and converge to the same result. Used primarily for collaborative text editing where character position matters.

SHOULD use OT only for text or sequence editing with a central server. For offline-first or peer-to-peer scenarios, prefer RGA CRDTs — OT requires all operations to pass through a central coordinator for ordering.

## Conflict Queues for Manual Resolution

When automated resolution is insufficient, queue conflicts for a human to resolve. MUST use this approach for medical records, legal documents, and financial transactions.

```sql
CREATE TABLE sync_conflicts (
    id            TEXT PRIMARY KEY NOT NULL,
    table_name    TEXT NOT NULL,
    record_id     TEXT NOT NULL,
    client_data   TEXT NOT NULL,   -- JSON of client version
    server_data   TEXT NOT NULL,   -- JSON of server version
    base_data     TEXT,            -- JSON of last-synced version (for 3-way merge)
    conflict_type TEXT NOT NULL,   -- 'update_update', 'update_delete', 'delete_update'
    detected_at   TEXT NOT NULL,
    resolved_at   TEXT,
    resolution    TEXT,            -- 'client', 'server', 'merged', 'discarded'
    resolved_data TEXT
);

CREATE INDEX idx_conflicts_unresolved
ON sync_conflicts(resolved_at) WHERE resolved_at IS NULL;
```

Detect conflicts by comparing the client's base version against the server's current version. If they differ, both sides changed since the last sync.

Apply the server version as an interim state while the conflict is pending, and surface a notification to the user.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
