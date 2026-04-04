---
name: rate-limiting
description: Honor `Retry-After` header on 429 responses; if no `Retry-After`, use exponential backoff; track `RateLimit-Remaining` p...
artifact: guidelines/networking/rate-limiting.md
version: 1.0.0
---

## Worker Focus
Honor `Retry-After` header on 429 responses; if no `Retry-After`, use exponential backoff; track `RateLimit-Remaining` proactively and slow down before hitting 429; queue and batch requests at the allowed rate rather than fire-and-retry

## Verify
429 responses trigger retry with `Retry-After` delay; no retry storm on 429 (exponential backoff enforced); `RateLimit-Remaining` monitoring present or proactive throttling implemented
