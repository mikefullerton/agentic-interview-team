---

id: cef41f52-bfc6-4ff0-bb67-eb52521c7391
title: "Retry and Resilience"
domain: agentic-cookbook://guidelines/implementing/networking/retry-and-resilience
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Not every failure is permanent. Retry transient failures with exponential backoff and jitter."
platforms: 
  - typescript
  - web
tags: 
  - networking
  - retry-and-resilience
depends-on: []
related: []
references: 
  - https://docs.aws.amazon.com/general/latest/gr/api-retries.html
  - https://learn.microsoft.com/en-us/azure/architecture/best-practices/transient-faults
  - https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - networking
  - error-handling
---

# Retry and Resilience

Not every failure is permanent. Retry transient failures with exponential backoff and jitter.

**Exponential backoff with full jitter:**
```
delay = random(0, min(max_delay, base * 2^attempt))
```

| Parameter | Default |
|-----------|---------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Base delay | 1 second |
| Max delay cap | 30 seconds |
| Max retries | 3-5 (idempotent), 0 (non-idempotent unless safe) |

**Retryable status codes:** 408, 429, 500 (idempotent only), 502, 503, 504.
Clients MUST respect `Retry-After` header on 429 and 503.

**Clients MUST NOT retry:** 400, 401, 403, 404, 409, 422 — these are deterministic failures.

**Circuit breaker** for cascading failure prevention:
- Track failure rate over a sliding window (e.g., 10 requests)
- Open circuit when failure rate exceeds threshold (e.g., 50%)
- Stay open for a cooldown period (e.g., 30 seconds)
- Half-open: allow 1 probe request to test recovery

References:
- [AWS: Exponential Backoff and Jitter](https://docs.aws.amazon.com/general/latest/gr/api-retries.html)
- [Microsoft: Transient Fault Handling](https://learn.microsoft.com/en-us/azure/architecture/best-practices/transient-faults)
- [Microsoft: Circuit Breaker Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
