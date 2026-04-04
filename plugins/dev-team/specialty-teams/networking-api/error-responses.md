---
name: error-responses
description: RFC 9457 Problem Details format with `Content-Type: application/problem+json`; required fields: `type` (URI), `title` (s...
artifact: guidelines/networking/error-responses.md
version: 1.0.0
---

## Worker Focus
RFC 9457 Problem Details format with `Content-Type: application/problem+json`; required fields: `type` (URI), `title` (stable), `status` (mirrors HTTP), `detail` (occurrence-specific), `instance`; extension fields (`errors`, `trace_id`) for machine-readable details

## Verify
All error responses use `application/problem+json` content type; `type` field is a URI; `status` matches HTTP response code; field-level errors use `errors` array; no plain-string error bodies
