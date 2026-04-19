---

id: 631b7b61-985a-4f5d-9c44-2cfbfdb9091b
title: "Error Responses"
domain: agentic-cookbook://guidelines/implementing/networking/error-responses
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Use [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457) format with"
platforms: []
tags: 
  - error-responses
  - networking
depends-on: []
related: []
references: 
  - https://www.rfc-editor.org/rfc/rfc9457
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - api-integration
  - error-handling
---

# Error Responses

Error responses MUST use [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457) format with
`Content-Type: application/problem+json`:

```json
{
  "type": "https://api.example.com/errors/validation",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request body contains 2 validation errors.",
  "instance": "/orders/abc-123",
  "errors": [
    { "field": "email", "message": "Must be a valid email address" },
    { "field": "age", "message": "Must be >= 0" }
  ]
}
```

- **type** (URI) — machine-readable error identifier (MUST be present)
- **title** — short human-readable summary (MUST be stable across occurrences)
- **status** — HTTP status code (MUST mirror response)
- **detail** — explanation specific to this occurrence
- **instance** — identifies the specific request
- Add extension fields (`errors`, `trace_id`) as needed

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
