---
name: real-time-communication
description: Start with SSE for server-push (built-in reconnection, standard HTTP, sufficient for 80%+ of real-time needs); WebSocket...
artifact: guidelines/networking/real-time-communication.md
version: 1.0.0
---

## Worker Focus
Start with SSE for server-push (built-in reconnection, standard HTTP, sufficient for 80%+ of real-time needs); WebSocket only when bidirectional streaming required; polling as fallback for very low frequency updates; reconnection with backoff required for persistent connections

## Verify
SSE used instead of WebSocket unless bidirectional streaming is required; reconnection logic present for SSE/WebSocket connections; reconnection uses backoff (not immediate retry loop)
