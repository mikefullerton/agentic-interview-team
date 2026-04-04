---
name: real-time-communication
description: Prefer SSE (`EventSource`) for server-push (notifications, live feeds, progress); WebSocket only for bidirectional strea...
artifact: guidelines/networking/real-time-communication.md
version: 1.0.0
---

## Worker Focus
Prefer SSE (`EventSource`) for server-push (notifications, live feeds, progress); WebSocket only for bidirectional streaming; SSE has built-in reconnection; polling as low-frequency fallback

## Verify
SSE used for unidirectional push; WebSocket only where bidirectional required and justified; EventSource reconnection not suppressed; polling interval ≥1min if used
