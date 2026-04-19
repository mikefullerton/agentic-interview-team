---

id: 3B9FCE69-7541-4F49-81AE-86119096A4D8
title: "Clock Systems for Sync"
domain: agentic-cookbook://guidelines/implementing/data/clock-systems
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-06
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "How to choose the right clock system for distributed sync: physical clocks, Lamport timestamps, vector clocks, Hybrid Logical Clocks, and server-assigned monotonic versions."
platforms:
  - sqlite
  - postgresql
tags:
  - database
  - sync
  - clocks
  - hlc
  - distributed-systems
depends-on: []
related:
  - guidelines/data/sqlite-best-practices.md
  - guidelines/data/conflict-resolution.md
  - guidelines/data/sync-schema-design.md
references:
  - https://sergeiturukin.com/2017/06/26/hybrid-logical-clocks.html
  - https://en.wikipedia.org/wiki/Vector_clock
  - https://www.yugabyte.com/blog/evolving-clock-sync-for-distributed-databases/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-06"
triggers:
  - database-operations
  - offline-support
  - schema-design
---

# Clock Systems for Sync

Sync systems need a reliable way to order events across distributed devices. The choice of clock system directly affects conflict resolution accuracy, storage overhead, and implementation complexity. Each system makes different trade-offs.

## Physical Clocks (Wall Time)

Wall-clock timestamps (`datetime('now')`, `Date.now()`, `System.currentTimeMillis()`) are simple but unreliable for ordering across devices.

**The problem:** Different devices have different clocks. NTP corrections, manual time changes, and clock drift can result in two devices disagreeing about which event came first — sometimes by seconds or more. A client with a fast clock will always "win" LWW conflicts regardless of actual operation order.

**When acceptable:**
- Single-user-per-record apps (no concurrent editing)
- The server assigns all timestamps (client clocks are never trusted for ordering)
- Ordering accuracy within a few seconds is sufficient

**MUST NOT use raw wall-clock time** as the sole ordering mechanism in multi-device collaborative apps.

## Lamport Timestamps

A monotonically increasing integer counter. Each event increments the counter by one. When a message arrives from another device with a higher counter value, the local counter jumps to that value.

**Property:** If event `e` happened before `f`, then `L(e) < L(f)`. But the converse is NOT guaranteed — `L(e) < L(f)` does NOT mean `e` happened before `f`. Lamport timestamps cannot distinguish "happened-before" from "concurrent."

**When to use:** Systems that only need causal ordering (not concurrency detection). Extremely low overhead — a single integer column. Suitable for server-to-client replication where the server serializes all writes.

**When NOT to use:** Conflict detection that requires distinguishing concurrent writes from causally ordered writes.

## Vector Clocks

An array of counters, one per device. When Device A sends a message, it includes its full vector. The recipient merges by taking the element-wise maximum.

**Property:** Can definitively distinguish "happened-before" from "concurrent." Two events are concurrent if neither vector dominates the other.

**Limitation:** Storage and transmission cost grows O(n) where n is the number of devices. With 10 devices, each record carries 10 counters. With thousands of devices (consumer apps), this is impractical.

**When to use:** Systems with a small, fixed set of replicas (e.g., 3–5 database nodes in a cluster). Well-suited for server-side distributed databases, not client-side mobile sync.

## Hybrid Logical Clocks (HLC)

HLC combines physical wall-clock time with a logical counter in a single 64-bit value:

```
HLC timestamp = [48-bit physical time ms] + [16-bit logical counter]
```

**Properties:**
- Stays close to wall-clock time (within a bounded drift of physical time)
- Guarantees causal ordering (strictly monotonic per node)
- Self-stabilizing: NTP corrections that move the clock backward do not violate monotonicity
- Single 64-bit value — no per-device array growth
- Human-readable: can be truncated to a millisecond timestamp for debugging

**Update rules:** When generating an event, take `max(local_physical_time, last_hlc_physical)`. If equal, increment the logical counter. When receiving a message with an HLC, merge: take the max of both physical components, then adjust the counter to avoid collision.

SHOULD use HLC as the default timestamp mechanism for multi-device sync. It provides the ordering guarantees of logical clocks while remaining close to physical time and fitting in a single `INTEGER` or `TEXT` column.

Store HLC values in SQLite as `INTEGER` (milliseconds + counter packed) or as `TEXT` with a fixed-width format that sorts lexicographically.

## Server-Assigned Monotonic Versions

Instead of relying on client clocks, the server assigns a strictly increasing version number to every accepted change using a database sequence.

```sql
-- PostgreSQL: monotonic sync version sequence
CREATE SEQUENCE sync_version_seq;

-- On every write accepted during sync:
UPDATE tasks
SET sync_version = nextval('sync_version_seq')
WHERE id = ?;
```

**Properties:**
- Zero clock-skew issues — the server is the sole authority on ordering
- Clients request delta pulls with `WHERE sync_version > ?` — simple and efficient
- Easy to reason about and debug
- Requires server connectivity to assign versions — not suitable for pure peer-to-peer

**When to use:** Client-server architectures where all writes are validated by the server. This is the most common pattern in production sync systems (Linear, Figma, and most mobile apps use variants of this). SHOULD be the default choice for centralized sync.

## Choosing the Right Clock

| Scenario | Recommended Clock |
|----------|------------------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Server assigns all timestamps | Physical clock (server-side) |
| Client-server sync with server authority | Server-assigned monotonic versions |
| Multi-device, causal ordering needed | Hybrid Logical Clocks (HLC) |
| Small fixed replica set (database cluster) | Vector clocks |
| Simple causal ordering, low overhead | Lamport timestamps |
| Peer-to-peer, no central server | HLC or CRDTs (which embed their own ordering) |

MUST NOT rely on SQLite's `datetime('now')` for conflict ordering in multi-device scenarios. Device clocks diverge. Use HLC or server-assigned versions instead.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-04-06 | Mike Fullerton | Initial version |
