---
name: timeouts-client
description: All fetch/XHR calls have connection timeout (10s), response timeout (30s), total lifecycle timeout (60-120s); no infinit...
artifact: guidelines/networking/timeouts.md
version: 1.0.0
---

## Worker Focus
All fetch/XHR calls have connection timeout (10s), response timeout (30s), total lifecycle timeout (60-120s); no infinite-wait fetch; long-running ops use 202 Accepted + polling

## Verify
`AbortController` or equivalent timeout set on all network requests; no `fetch()` without timeout; long-running endpoints use polling not extended timeout
