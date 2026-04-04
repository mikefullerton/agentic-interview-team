---
name: rate-limiting
description: Emit `Retry-After` header on 429 responses; expose `RateLimit-Remaining`/`RateLimit-Reset` headers proactively; apply pe...
artifact: guidelines/networking/rate-limiting.md
version: 1.0.0
---

## Worker Focus
Emit `Retry-After` header on 429 responses; expose `RateLimit-Remaining`/`RateLimit-Reset` headers proactively; apply per-client rate limits; queue-friendly (batching preferred over fire-and-retry)

## Verify
429 responses include `Retry-After` header; `RateLimit-Remaining` emitted on responses to rate-limited routes; rate limits applied per API key or authenticated user
