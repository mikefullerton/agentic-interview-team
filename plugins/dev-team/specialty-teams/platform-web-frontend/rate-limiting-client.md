---
name: rate-limiting-client
description: Honor `Retry-After` header on 429; track `RateLimit-Remaining` and throttle proactively; queue/batch requests at allowed...
artifact: guidelines/networking/rate-limiting.md
version: 1.0.0
---

## Worker Focus
Honor `Retry-After` header on 429; track `RateLimit-Remaining` and throttle proactively; queue/batch requests at allowed rate; never fire-and-retry in a loop

## Verify
429 response triggers wait using `Retry-After`; no tight retry loops without backoff; client reads `RateLimit-Remaining` if available
