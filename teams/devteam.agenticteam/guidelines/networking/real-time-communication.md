---

id: 2e317c68-384d-46b8-b3b3-0bcc6602e545
title: "Real-Time Communication"
domain: agentic-cookbook://guidelines/implementing/networking/real-time-communication
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Choose the simplest technique that meets your needs."
platforms: 
  - web
tags: 
  - networking
  - real-time-communication
depends-on: []
related: []
references: 
  - https://developer.mozilla.org/en-US/docs/Web/API/EventSource
  - https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
  - https://www.rfc-editor.org/rfc/rfc6455
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - networking
  - concurrency
---

# Real-Time Communication

Choose the simplest technique that meets your needs.

| Technique | Direction | Use When |
|-----------|-----------|----------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Polling | Client-pull | Low frequency (<1/min), simplicity paramount |
| SSE | Server-push | Notifications, live feeds, dashboards, progress |
| WebSocket | Bidirectional | Chat, multiplayer, collaborative editing |

**Start with SSE** for server-push — it has built-in reconnection, works over standard HTTP,
and is sufficient for 80%+ of "real-time" needs. WebSocket SHOULD only be used when
bidirectional streaming is required. Polling MAY be used as a fallback for very low frequency updates.

References:
- [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
- [MDN: WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [RFC 6455: WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
