---
name: retry-and-resilience
description: Exponential backoff with full jitter (`random(0, min(max_delay, base * 2^attempt))`); base 1s, max cap 30s, 3-5 retries ...
artifact: guidelines/networking/retry-and-resilience.md
version: 1.0.0
---

## Worker Focus
Exponential backoff with full jitter (`random(0, min(max_delay, base * 2^attempt))`); base 1s, max cap 30s, 3-5 retries for idempotent, 0 for non-idempotent; retryable: 408/429/500(idempotent)/502/503/504; never retry 400/401/403/404/409/422; circuit breaker for cascading failure prevention

## Verify
Retry logic only applies to retryable status codes; non-idempotent requests not retried on 500; exponential backoff with jitter implemented (no fixed-interval retry); circuit breaker present or explicitly scoped out
