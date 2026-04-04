---
name: retry-and-resilience
description: Idempotent endpoints (GET, PUT, DELETE) safe to retry; POST endpoints idempotency keys where needed; server-side circuit...
artifact: guidelines/networking/retry-and-resilience.md
version: 1.0.0
---

## Worker Focus
Idempotent endpoints (GET, PUT, DELETE) safe to retry; POST endpoints idempotency keys where needed; server-side circuit breaker for upstream dependencies; 503 includes `Retry-After`

## Verify
GET/PUT/DELETE are idempotent as implemented; 503 responses include `Retry-After`; upstream dependency failures return 503 (not 500); circuit breaker state logged
