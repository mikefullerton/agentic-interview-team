---
name: real-time-communication
description: SSE endpoints for server-push (notifications, live feeds, progress); WebSocket only for bidirectional streaming; SSE use...
artifact: guidelines/networking/real-time-communication.md
version: 1.0.0
---

## Worker Focus
SSE endpoints for server-push (notifications, live feeds, progress); WebSocket only for bidirectional streaming; SSE uses standard `text/event-stream` with reconnection semantics; polling endpoints available as fallback

## Verify
SSE endpoint uses `Content-Type: text/event-stream`; Last-Event-ID reconnection supported; WebSocket upgrade only where bidirectional justified; long-polling not used where SSE suffices
