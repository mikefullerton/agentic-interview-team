---
name: access-patterns-compliance
description: 8 compliance checks — api-design-conventions (RESTful with versioning), offline-behavior (defined behavior when network ...
artifact: compliance/access-patterns.md
version: 1.0.0
---

## Worker Focus
8 compliance checks — api-design-conventions (RESTful with versioning), offline-behavior (defined behavior when network unavailable), retry-with-backoff (exponential backoff + jitter on failure), timeout-configuration (no indefinite waits), rate-limit-handling (HTTP 429 + Retry-After respected), pagination-support (collection endpoints paginated), reconnection-strategy (WebSocket/SSE reconnect with backoff), error-response-handling (all documented error codes handled)

## Verify
Each compliance check has a status with evidence; retry implementation uses exponential backoff with jitter; all network calls have explicit timeouts; HTTP 429 handling present if rate-limited APIs are consumed
