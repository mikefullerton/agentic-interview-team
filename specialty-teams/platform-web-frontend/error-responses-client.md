---
name: error-responses-client
description: Parse RFC 9457 Problem Details (`application/problem+json`); display `detail` field to user; surface `errors[]` field fo...
artifact: guidelines/networking/error-responses.md
version: 1.0.0
---

## Worker Focus
Parse RFC 9457 Problem Details (`application/problem+json`); display `detail` field to user; surface `errors[]` field for field-level validation; include `instance`/`trace_id` in error reports

## Verify
Client parses `application/problem+json`; field errors from `errors[]` shown inline; no raw status codes shown to user; error UI includes recovery action
