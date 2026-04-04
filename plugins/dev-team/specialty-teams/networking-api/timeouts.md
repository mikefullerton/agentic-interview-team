---
name: timeouts
description: Always set both connection timeout (10s) and read/response timeout (30s); total/request timeout 60-120s including retrie...
artifact: guidelines/networking/timeouts.md
version: 1.0.0
---

## Worker Focus
Always set both connection timeout (10s) and read/response timeout (30s); total/request timeout 60-120s including retries; never use infinite timeouts; long-running operations use 202 Accepted + polling pattern instead of extended timeouts

## Verify
Connection timeout ≤10s configured; read timeout ≤30s configured; no requests with infinite (0/null) timeout; operations expected to take >30s return 202 Accepted with polling endpoint
