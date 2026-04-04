---
name: offline-and-connectivity
description: Local-first design with background sync; optimistic updates with rollback on server failure; queue-based outbox for muta...
artifact: guidelines/networking/offline-and-connectivity.md
version: 1.0.0
---

## Worker Focus
Local-first design with background sync; optimistic updates with rollback on server failure; queue-based outbox for mutations drained on reconnect; conflict detection via ETags/version numbers with 409 response; `last_synced_at` per entity for delta sync; clear connectivity status shown to user; user work never silently discarded

## Verify
Offline mutations queued and not silently dropped; optimistic UI rolled back on server error; connectivity status visible to user; `last_synced_at` tracked per synced entity; conflict scenarios return 409 with both versions; offline scenarios tested (airplane mode, flaky connections)
