---
name: timeouts
description: All outbound HTTP calls have connection timeout (10s), read timeout (30s), total lifecycle timeout (60-120s); long-runni...
artifact: guidelines/networking/timeouts.md
version: 1.0.0
---

## Worker Focus
All outbound HTTP calls have connection timeout (10s), read timeout (30s), total lifecycle timeout (60-120s); long-running operations use 202 Accepted + status polling endpoint; no infinite-wait calls to downstream services

## Verify
All `requests`/`httpx`/similar calls have `timeout=` set; no `timeout=None`; long-running tasks return 202 with status URL; no blocking calls without upper bound
