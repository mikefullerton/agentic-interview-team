---
title: "Sync Case Studies"
domain: database
type: guideline
status: draft
created: 2026-04-06
modified: 2026-04-06
author: Mike Fullerton
summary: "Real-world sync architectures from production systems: Notion, Linear, Figma, Temporal, and platform-specific patterns for mobile and desktop"
tags:
  - database
  - sync
  - architecture
  - case-study
references:
  - https://www.notion.com/blog/how-we-sped-up-notion-in-the-browser-with-wasm-sqlite
  - https://github.com/wzhudev/reverse-linear-sync-engine
  - https://www.figma.com/blog/how-figmas-multiplayer-technology-works/
  - https://docs.expo.dev/guides/local-first/
  - https://rxdb.info/electron-database.html
  - https://developer.android.com/training/data-storage/room
related:
  - sync-strategies.md
  - sync-sqlite.md
  - decision-frameworks.md
---

# Sync Case Studies

> Real-world sync architectures from production systems and platform-specific implementation patterns.

---

## Table of Contents

1. [Notion](#1-notion)
2. [Linear](#2-linear)
3. [Figma](#3-figma)
4. [Temporal (Kotlin Multiplatform)](#4-temporal-kotlin-multiplatform)
5. [Mobile Apps (iOS/Android)](#5-mobile-apps-iosandroid)
6. [Desktop Apps (Electron / Tauri)](#6-desktop-apps-electron--tauri)

---

## 26. Real-World Sync Architectures

### 26.1 Notion

**Architecture:** Notion built their entire client-side data layer on SQLite compiled to WebAssembly.

**Key design decisions:**
- Uses OPFS SyncAccessHandle Pool VFS for browser persistence
- SharedWorker coordinates SQLite access across browser tabs -- only one tab writes at a time
- Web Locks API detects closed tabs
- The local SQLite database serves as a read cache; the server is source of truth
- Every server update writes to the local cache
- Navigation queries race SQLite and API requests on slower devices

**Performance results:**
- 20% improvement in page navigation times across all browsers
- 28-33% faster for users in high-latency regions (Australia, China, India)

**Notable trade-off:** Initial page load deliberately skips SQLite caching because downloading the WASM library is slower than the first API call. SQLite only accelerates subsequent navigations.

**Source:** [How We Sped Up Notion with WASM SQLite (Notion Blog)](https://www.notion.com/blog/how-we-sped-up-notion-in-the-browser-with-wasm-sqlite)

### 26.2 Linear

**Architecture:** Custom sync engine with centralized server authority.

**Key design decisions:**
- All operations pass through the server, which assigns sequential sync IDs (monotonically increasing integers)
- Sync IDs serve as the global version number of the database
- Clients send transactions to the server; server broadcasts delta packets to all clients
- Delta packets may differ from the original transaction (server can add side-effects)
- Uses MobX for reactive UI updates from local store
- IndexedDB for browser-side persistence

**Data model:**
- Models defined with TypeScript decorators (`@ClientModel`)
- Seven property types: property, ephemeralProperty, reference, referenceModel, referenceCollection, backReference, referenceArray
- Lazy loading for properties not needed at bootstrap
- Schema hash for instant detection of schema mismatches

**Offline support:**
- Transactions cached in IndexedDB during disconnection
- Automatically resent on reconnection
- Reversible transactions enable client-side rollback if server rejects

**Conflict resolution:** Last-writer-wins for simple fields; server-authoritative ordering via sync IDs eliminates most conflicts by serializing all operations.

**Sources:**
- [Reverse Engineering Linear's Sync Engine (GitHub)](https://github.com/wzhudev/reverse-linear-sync-engine)
- [Linear local-first rabbit hole (Bytemash)](https://bytemash.net/posts/i-went-down-the-linear-rabbit-hole/)

### 26.3 Figma

**Architecture:** Client/server with custom CRDT-inspired approach.

**Key design decisions:**
- Clients connect to servers via WebSockets
- Each document gets a separate server process
- Inspired by CRDTs but not a pure CRDT implementation
- Uses server authority for operation ordering (closer to OT than full CRDT)
- CRDTs provide eventual consistency guarantees: if no more updates, all clients converge

**Collaboration model:**
- Server receives operations, validates against authoritative state
- Transforms operations to resolve concurrent conflicts
- Broadcasts transformed operations to all connected clients
- Client-side operations are applied optimistically (instant UI)

**Source:** [How Figma's Multiplayer Technology Works (Figma Blog)](https://www.figma.com/blog/how-figmas-multiplayer-technology-works/)

### 26.4 Mobile Apps (iOS/Android)

**iOS pattern (Core Data + CloudKit):**
- `NSPersistentCloudKitContainer` bridges Core Data (backed by SQLite) with iCloud
- Only SQLite-type persistent stores can be synchronized
- Requires Persistent History Tracking enabled
- Supports three database tiers: private, shared, public
- Multiple SQLite stores with separate configurations control what syncs

**Android pattern (Room + Sync Adapter):**
- Room provides a type-safe abstraction over SQLite
- SyncAdapter framework handles background sync with system-managed scheduling
- ContentProvider mediates between SyncAdapter and the private SQLite database
- System batches sync operations for battery efficiency

**Cross-platform pattern (React Native / Flutter):**
- SQLite via `expo-sqlite` or `sqflite` packages
- Outbox queue table for pending mutations
- NetInfo API to detect connectivity changes
- Background sync on reconnect
- PowerSync or ElectricSQL for managed sync infrastructure

### 26.5 Desktop Apps (Electron / Tauri)

**Electron:**
- better-sqlite3 or sql.js for SQLite access
- RxDB provides reactive queries with IndexedDB or SQLite adapters
- Sync via REST APIs or WebSocket connections
- Multiple windows share one SQLite database via main process IPC

**Tauri:**
- Rust backend with `sqlx` crate for direct SQLite access
- Tauri SQL plugin for cross-platform SQLite
- Drizzle ORM: frontend computes SQL queries, sends to Rust backend for execution
- Turso embedded replicas for managed sync

**Shared desktop pattern:**
- SQLite database in the app's data directory
- WAL mode enabled for concurrent read/write
- Sync worker runs in a background thread
- Outbox pattern for offline writes
- Delta sync for efficient bandwidth usage

**Sources:**
- [Expo SQLite Guide (Expo Documentation)](https://docs.expo.dev/guides/local-first/)
- [Electron Database (RxDB)](https://rxdb.info/electron-database.html)
- [Drizzle + SQLite in Tauri (DEV)](https://dev.to/huakun/drizzle-sqlite-in-tauri-app-kif)
- [Android Room Database (Android Developers)](https://developer.android.com/training/data-storage/room)


---

## 4. Temporal (Kotlin Multiplatform)

**Architecture:** Offline-first cross-platform app (iOS, macOS, Android, Windows, web) with a centralized Ktor backend and PostgreSQL, syncing to client-side SQLite databases via Kotlin Multiplatform shared code.

**Hosting:** Railway (~$12/mo) — Ktor fat JAR + managed PostgreSQL.

### Sync Protocol

Combined push/pull in a single round trip:

```
POST /api/sync/v2

Request:  { lastSyncVersion, contents: [...], projects: [...], edits: [...], calendarEvents: [...] }
Response: { currentSyncVersion, contents: [...], projects: [...], edits: [...], calendarEvents: [...] }
```

### Conflict Resolution

**Last-write-wins (LWW)** based on `updatedAt` timestamps:
1. No server record exists → INSERT, assign `syncVersion` from PostgreSQL sequence
2. Server record exists, client `updatedAt` is newer → UPDATE
3. Server record exists, server `updatedAt` is newer → skip (server wins)

### Key Design Decisions

- **UUID primary keys** — enables offline creation on any device without ID collisions
- **Soft deletes** (`isDeleted` flag) — tombstones propagate deletions across devices
- **Server `syncVersion`** (PostgreSQL sequence, monotonic) — efficient delta pulls without clock-skew issues
- **Client `isDirty` flag** per record — simple dirty tracking without a change log
- **Field-level edit tracking** — `LocalEditRepository` records edits with timestamps and device IDs for fine-grained conflict detection
- **Entity-agnostic infrastructure** — new content types added by implementing `Syncable` interface
- **CRUD routes preserved** alongside `/api/sync` — CRUD for web/admin, sync for offline-capable clients

### Client Sync Engine (SyncEngineV2)

```
1. Collect unsynced records from all content types (isDirty = true)
2. Collect unsynced edits from LocalEditRepository
3. Read lastSyncVersion from local metadata
4. POST /api/sync/v2
5. Upsert response records locally via content type handlers
6. Rebuild snapshots for affected entities (SnapshotBuilder)
7. Store new currentSyncVersion
```

### Server Sync Processing (SyncServiceV2)

```
1. For each entity type in request, process dirty records with upsertWithLWW()
2. Assign syncVersion from PostgreSQL sequence on every INSERT/UPDATE
3. Return all records where syncVersion > client's lastSyncVersion
4. Include edit operations in response for field-level merge support
```

### Background Sync

- **DaemonSyncScheduler** — configurable interval (default 30 seconds), async coroutine-based
- **Platform-specific daemons:**
  - macOS: XPC service for background sync
  - Windows: TCP-based daemon (port 19847) with JSON-RPC protocol
- **Shared daemon logic** across platforms via Kotlin Multiplatform

### Architecture Layers

```
┌───────────────────────────────────────────┐
│  Platform UI (SwiftUI / Compose / React)  │
├───────────────────────────────────────────┤
│  Shared KMP Module                        │
│  ├── SyncEngineV2 (orchestrator)          │
│  ├── SyncableInterface (per-entity)       │
│  ├── SyncPayloadAdapter (marshaling)      │
│  ├── SnapshotBuilder (state rebuild)      │
│  ├── LocalEditRepository (edit tracking)  │
│  └── DaemonSyncScheduler (periodic sync)  │
├───────────────────────────────────────────┤
│  Ktor Backend                             │
│  ├── SyncServiceV2 (LWW processing)       │
│  ├── SyncOperations (generic interface)   │
│  └── SyncRoutesV2 (POST /api/sync/v2)    │
├───────────────────────────────────────────┤
│  PostgreSQL (source of truth)             │
│  └── Monotonic sync_version sequence      │
└───────────────────────────────────────────┘
```

### Key Takeaways

1. **Single round trip** — combined push/pull minimizes latency on mobile networks
2. **Monotonic server versions** — eliminates clock-skew issues entirely for ordering
3. **isDirty flag simplicity** — no change log table, no triggers, just a boolean per record
4. **Entity-agnostic design** — `Syncable` interface means adding a new entity type requires minimal boilerplate
5. **Edit operations as first-class** — field-level edit history enables future upgrade to field-level merge without protocol changes
6. **Snapshot rebuilding** — derived state is rebuilt after sync, not stored and synced separately

**Source:** Production implementation in `../temporal/` — see `shared/src/commonMain/kotlin/company/temporal/shared/sync/` and `backend/src/main/kotlin/company/temporal/backend/sync/`

