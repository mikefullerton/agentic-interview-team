---

id: A0CB2815-8FDD-450A-AF46-8FCA80BA1ABA
title: "Sync Engine Design"
domain: agentic-cookbook://guidelines/implementing/data/sync-engine-design
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "How to design a client-side sync engine: layered architecture, entity-agnostic Syncable interface, the six-step sync cycle, scheduling strategies, snapshot rebuilding, and error handling with circuit breakers."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - sync
  - architecture
  - engine
  - error-handling
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
  - guidelines/data/sync-protocol.md
  - guidelines/data/offline-first-architecture.md
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - offline-support
  - database-operations
---

# Sync Engine Design

The sync engine is the client-side component that orchestrates all synchronization: collecting dirty records, sending them to the server, receiving server changes, applying them locally, and managing retry and scheduling. A well-designed engine is entity-agnostic — adding a new synced entity type requires minimal new code.

## Architecture Layers

Separate concerns into four layers:

```
┌──────────────────────────────────┐
│           Application            │
│  (reads local DB, writes through │
│   sync-aware mutations)          │
├──────────────────────────────────┤
│         Sync Orchestrator        │
│  (coordinates push/pull cycles,  │
│   manages sync state/versions)   │
├──────────────────────────────────┤
│       Content Type Handlers      │
│  (per-entity sync logic: what    │
│   to collect, how to upsert)     │
├──────────────────────────────────┤
│          Sync Transport          │
│  (HTTP client, WebSocket, SSE)   │
├──────────────────────────────────┤
│         Local Database           │
│  (SQLite with WAL mode)          │
└──────────────────────────────────┘
```

The **Application** layer reads from local SQLite exclusively. It never fetches from the network directly.

The **Orchestrator** coordinates the sync cycle, manages the checkpoint (last sync version), and dispatches to registered content type handlers.

The **Content Type Handlers** implement entity-specific logic: what queries collect dirty records, how to serialize for the API, and how to apply server responses.

The **Transport** layer handles HTTP/WebSocket communication, authentication, and raw retry mechanics.

## Entity-Agnostic Syncable Interface

SHOULD design the engine so every synced entity implements a common interface:

```
interface Syncable<T> {
    collectDirty(): List<T>           // query local records where isDirty = true
    buildPayload(items: List<T>)      // serialize for sync request body
    applyResponse(items: List<T>)     // upsert server records locally
    markSynced(items: List<T>)        // clear dirty flags, update last_synced_at
}
```

The orchestrator iterates over all registered content types without knowing their entity-specific details. Conflict handling MAY be customized per content type while sharing a common transport and scheduling layer.

Benefits: sync logic is tested once in the orchestrator; adding a new entity is a single interface implementation; entity-specific quirks are contained.

## The Sync Cycle

A standard bidirectional sync cycle SHOULD complete in a single server round trip:

```
1. Collect    — Query all registered entities for dirty (isDirty = 1) records
2. Package    — Build request body: { lastSyncVersion, dirtyRecords[] }
3. Send       — POST /api/sync (one endpoint handles all entity types)
4. Receive    — Server returns: { currentSyncVersion, changedRecords[] }
5. Apply      — Upsert server records locally, clear dirty flags
6. Checkpoint — Store currentSyncVersion; use as since_version on next sync
```

Combining push and pull into one HTTP request halves network round trips compared to separate push and pull calls — significant on mobile networks with 200–800ms latency.

After step 5, rebuild any derived views or computed state that depends on the synced entities before notifying the UI of changes.

## Dirty Tracking Strategies

SHOULD start with `isDirty` flag columns — simple, low overhead, works everywhere:

```sql
-- Set on every local INSERT/UPDATE
UPDATE tasks SET is_dirty = 1, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
WHERE id = ?;

-- Clear after successful sync
UPDATE tasks SET is_dirty = 0, last_synced_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
WHERE id IN (...);
```

Upgrade to a **change-log table** (populated via triggers) only if you need operation-type awareness (INSERT vs UPDATE vs DELETE) or ordered change history for field-level merge.

Upgrade to an **edit operations table** (field-level deltas with timestamps and device IDs) only if the server needs to perform three-way field merges.

## Sync Scheduling

SHOULD implement at least two scheduling modes:

**Periodic:** Run the sync cycle every N seconds (e.g., 30s) while the app is active. Simple, predictable, battery-friendly. Use as the safety net to catch any missed event-driven syncs.

**Event-driven:** Trigger a sync immediately after a user mutation (or after a batch of mutations within a short debounce window). More responsive but can burst traffic — always throttle with a minimum interval between syncs (e.g., no more than once per 2 seconds).

**Background daemon:** Use platform-specific APIs to sync when the app is closed:
- iOS/macOS: Background App Refresh or XPC service
- Android: WorkManager with network constraints
- Web: Service Worker Periodic Sync API

**Connectivity-aware:** Pause sync when offline. Resume immediately on reconnection, then fall back to the periodic schedule.

## Snapshot Rebuilding

After applying sync changes, some entities require derived state to be rebuilt before the UI can display accurate data:

```
1. Receive server changes for entity X
2. Upsert raw records into local DB (inside a transaction)
3. Rebuild computed views, aggregates, or snapshots that depend on entity X
4. Notify the UI layer of changes (e.g., via reactive query, live query, or notification)
```

This matters especially for entities with edit history: the current visible state may be a function of applying all edits in sequence, not just the latest record. MUST rebuild snapshots in the correct dependency order when multiple entity types are synced in the same cycle.

## Error Handling

**Exponential backoff with jitter:** Apply to all transient failures.

```
delay = min(MAX_DELAY, BASE_DELAY * 2^attempt) + random(0, JITTER)
```

Typical values: `BASE_DELAY = 1s`, `MAX_DELAY = 15min`, `JITTER = 0–1s`.

**Retry categories:**

| Error | Action |
|-------|--------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Network timeout, 503 | Retry with backoff |
| 400, 401, 403 | Do not retry — surface to user |
| 409 Conflict | Apply conflict resolution strategy, then retry |
| 500 | Retry with longer backoff |

**Circuit breaker:** After N consecutive sync failures (e.g., 5), stop retrying automatically. Enter a degraded mode: the app continues to work offline, changes queue locally. Resume sync only after a cooldown period (e.g., 30 minutes) or explicit user action. Log the failure reason for diagnostics.

MUST surface persistent sync failures to the user — never silently fail. A status indicator showing "Sync paused — check connection" is acceptable; silently losing changes is not.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
