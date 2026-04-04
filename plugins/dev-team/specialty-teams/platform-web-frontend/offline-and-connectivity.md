---
name: offline-and-connectivity
description: Optimistic updates for most cases; outbox queue for mutations during offline; clear connectivity status indicator; no si...
artifact: guidelines/networking/offline-and-connectivity.md
version: 1.0.0
---

## Worker Focus
Optimistic updates for most cases; outbox queue for mutations during offline; clear connectivity status indicator; no silent discard of user work; Service Worker for offline asset serving if needed

## Verify
Connectivity status shown to user; mutations queued when offline and retried on reconnect; no user-initiated action silently discarded; optimistic update rolled back on server failure
