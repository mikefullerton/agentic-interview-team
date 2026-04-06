---
title: "Decision Frameworks"
domain: database
type: guideline
status: draft
created: 2026-04-03
modified: 2026-04-06
author: Mike Fullerton
summary: "Decision trees for choosing sync strategies, sync tools, schema patterns, and database architecture"
tags:
  - database
  - sync
  - decision-framework
related:
  - sync-strategies.md
  - sync-sqlite.md
  - sync-case-studies.md
  - schema-design.md
---

# Decision Frameworks

> Decision trees for choosing sync strategies, sync tools, schema patterns, and database architecture.

---

## 1. Choosing a Sync Strategy

```
Is the server always the source of truth?
├── YES: Pull-only sync (server-wins)
│   └── Tools: PowerSync, Turso embedded replicas
└── NO: Bidirectional sync needed
    │
    Can you tolerate silent data loss on conflict?
    ├── YES: Last-Write-Wins
    │   └── Simple timestamp-based resolution
    └── NO:
        │
        Do users edit the same fields concurrently?
        ├── RARELY: Field-level merge
        │   └── Three-way merge with base version
        ├── OFTEN: CRDTs or OT
        │   └── Tools: cr-sqlite, ElectricSQL, sqlite-sync
        └── NEVER (single-user-per-record): Version-based optimistic concurrency
            └── Conflict queue for edge cases
```

## 2. Choosing a Sync Tool

```
Do you need custom business logic on writes?
├── YES: PowerSync (your backend handles writes)
└── NO:
    │
    Is your server database Postgres?
    ├── YES:
    │   ├── Want CRDTs? → ElectricSQL
    │   ├── Want control? → PowerSync
    │   └── Want simplicity? → Turso + embedded replicas
    └── NO / Multiple DBs:
        ├── SQLite-to-SQLite: cr-sqlite or sqlite-sync
        ├── Need backup only: Litestream
        └── Custom: SQLite Session Extension + your own sync layer
```

## 3. Choosing a Clock System

```
Is there a central server that validates all writes?
├── YES: Server-assigned monotonic versions
│   └── Simplest, no clock-skew issues
│   └── Used by: Linear, Temporal, most mobile apps
└── NO (peer-to-peer or multi-master):
    │
    Do you need to detect concurrent edits?
    ├── YES:
    │   ├── Small replica set (< 10): Vector clocks
    │   └── Large/dynamic replica set: HLC (Hybrid Logical Clocks)
    └── NO (causal ordering sufficient):
        └── Lamport timestamps
```

## 4. Choosing a Conflict Resolution Pattern

```
What is the domain's tolerance for data loss?

HIGH tolerance (analytics, logs, preferences):
└── Last-Write-Wins — simplest, acceptable loss

MEDIUM tolerance (task trackers, CRMs, notes):
├── Do users edit different fields of the same record?
│   ├── YES: Field-level merge (three-way)
│   └── NO: LWW with conflict notification
└── Is the data single-user-per-record?
    └── YES: Optimistic concurrency (version check)

ZERO tolerance (medical, legal, financial):
└── Conflict queue for manual resolution
    └── Server queues both versions, human decides
```

## 5. Local Database vs Server Database Design

```
Does the app need offline support?
├── NO: Server DB only (PostgreSQL/MySQL)
│   └── Standard CRUD API, no sync complexity
└── YES: Local DB + Server DB + Sync
    │
    What platforms?
    ├── iOS only: Core Data + CloudKit
    ├── Android only: Room + SyncAdapter
    ├── Cross-platform:
    │   ├── Local: SQLite (via platform wrapper)
    │   ├── Server: PostgreSQL (recommended)
    │   └── Sync: Custom engine or managed (PowerSync/ElectricSQL)
    └── Web only:
        ├── IndexedDB + REST API
        └── Or: SQLite WASM + sync (Notion pattern)
    │
    Schema design for sync:
    ├── UUID primary keys (UUIDv7 recommended)
    ├── Soft deletes (is_deleted flag)
    ├── Change tracking (isDirty flag or change log)
    ├── Timestamps (created_at, updated_at, last_synced_at)
    └── Version column for optimistic concurrency
```

## 6. Schema Design Pattern Selection

```
How variable are the entity's attributes?

FIXED (known columns, rarely change):
└── Standard normalized tables
    └── Use STRICT tables for type safety (SQLite 3.37+)

MOSTLY FIXED with some variable attributes:
└── Typed columns for core fields + JSON column for extras
    └── Generated columns + indexes for queried JSON fields

HIGHLY VARIABLE (unknown attributes at design time):
├── Few queries on attributes: JSON column
└── Many queries on attributes: EAV pattern (last resort)

How deep is the entity hierarchy?

FLAT (no parent-child):
└── Standard tables with foreign keys

SHALLOW (1-2 levels):
└── Adjacency list (parent_id column)

DEEP or FREQUENT ancestor/descendant queries:
├── Read-heavy, rarely modified: Nested sets
├── Read-heavy, frequently modified: Closure table
└── Moderate reads, simple implementation: Adjacency list + recursive CTE
```

---

*Compiled from production sync implementations and database design best practices. Last updated April 2026.*
