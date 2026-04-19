---

id: c3883e6e-3bce-4bb9-a3be-61509a139288
title: "Timeouts"
domain: agentic-cookbook://guidelines/implementing/networking/timeouts
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Always set both connection and read timeouts. Never use infinite timeouts."
platforms: []
tags: 
  - networking
  - timeouts
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - networking
  - api-integration
---

# Timeouts

Every request MUST set both connection and read timeouts. Infinite timeouts MUST NOT be used.

| Timeout | Purpose | Default |
|---------|---------|---------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Connection | TCP + TLS handshake | 10 seconds |
| Read / Response | Time to first byte | 30 seconds |
| Total / Request | Entire lifecycle including retries | 60-120 seconds |

For long-running operations, use **202 Accepted** + polling pattern instead of extending
timeouts.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
