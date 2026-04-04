---
name: api-design
description: REST conventions — lowercase-hyphenated plural-noun URLs, max 2-level nesting, no verbs in URLs, correct HTTP methods wi...
artifact: guidelines/networking/api-design.md
version: 1.0.0
---

## Worker Focus
REST conventions — lowercase-hyphenated plural-noun URLs, max 2-level nesting, no verbs in URLs, correct HTTP methods with idempotency, right status codes (201+Location for POST, 204 for DELETE, 409 for conflict, 422 for validation), URL-path versioning

## Verify
No verbs in URL paths; collections are plural nouns; POST returns 201 with Location header; DELETE returns 204; 422 used for validation errors (not 400); version in URL path (`/v1/...`)
