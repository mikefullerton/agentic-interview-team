---
name: access-patterns-compliance
description: 8 compliance checks — api-design-conventions, offline-behavior, retry-with-backoff, timeout-configuration, rate-limit-ha...
artifact: compliance/access-patterns.md
version: 1.0.0
---

## Worker Focus
8 compliance checks — api-design-conventions, offline-behavior, retry-with-backoff, timeout-configuration, rate-limit-handling, pagination-support, reconnection-strategy, error-response-handling

## Verify
Each check has status with evidence; all collection endpoints paginated; all outbound calls have timeouts; 429 handling with Retry-After documented
