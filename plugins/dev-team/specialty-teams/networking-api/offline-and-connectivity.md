---
name: offline-and-connectivity
description: Local-first with background sync for offline apps; three patterns in complexity order — optimistic updates (rollback on ...
artifact: guidelines/networking/offline-and-connectivity.md
version: 1.0.0
---

## Worker Focus
Local-first with background sync for offline apps; three patterns in complexity order — optimistic updates (rollback on failure), queue-based sync (outbox drained on reconnect), conflict resolution (ETags/version numbers, 409 with both versions); track `last_synced_at`, show connectivity status, never silently discard user work

## Verify
Offline mutations go to an outbox queue rather than being discarded; connectivity status visible to user; failed sync items remain in queue for retry; conflict resolution strategy documented (server-wins, merge UI, or CRDT)
