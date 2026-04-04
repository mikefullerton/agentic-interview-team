---
name: error-responses
description: RFC 9457 Problem Details format with `Content-Type: application/problem+json`; machine-readable `type` URI, stable `titl...
artifact: guidelines/networking/error-responses.md
version: 1.0.0
---

## Worker Focus
RFC 9457 Problem Details format with `Content-Type: application/problem+json`; machine-readable `type` URI, stable `title`, mirrored `status`, occurrence-specific `detail`, `instance`, and extension fields (`errors[]`, `trace_id`)

## Verify
All error responses use `application/problem+json`; `type` is a URI; `status` mirrors HTTP status code; `errors[]` present for validation failures with field-level messages; no stack traces in response body
