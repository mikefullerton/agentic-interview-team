---
name: retry-and-resilience-client
description: Exponential backoff with full jitter for transient failures (408, 429, 500, 502, 503, 504); max 3-5 retries for idempote...
artifact: guidelines/networking/retry-and-resilience.md
version: 1.0.0
---

## Worker Focus
Exponential backoff with full jitter for transient failures (408, 429, 500, 502, 503, 504); max 3-5 retries for idempotent, 0 for non-idempotent; never retry 400/401/403/404/422; circuit breaker for cascading failures

## Verify
Retry logic only on retryable status codes; non-idempotent requests (POST) not retried by default; backoff includes jitter; circuit breaker or similar prevents cascading
