---
name: offline-and-connectivity
description: Server supports ETag/version numbers for conflict detection (409 with both versions); delta sync via `last_synced_at`; o...
artifact: guidelines/networking/offline-and-connectivity.md
version: 1.0.0
---

## Worker Focus
Server supports ETag/version numbers for conflict detection (409 with both versions); delta sync via `last_synced_at`; outbox queue patterns on client enabled by server returning reliable mutation acknowledgment

## Verify
Conflict scenarios return 409 with current server state; ETag or version field on mutable resources; delta sync endpoints accept `since` parameter
