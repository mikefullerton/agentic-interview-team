---
name: api-design
description: REST with consistent URL conventions (lowercase-hyphen, plural nouns, max 2 nesting levels, no verbs, no trailing slashe...
artifact: guidelines/networking/api-design.md
version: 1.0.0
---

## Worker Focus
REST with consistent URL conventions (lowercase-hyphen, plural nouns, max 2 nesting levels, no verbs, no trailing slashes), correct HTTP method semantics and idempotency, correct status codes, URL path versioning (`/v1/`) bumped only on breaking changes

## Verify
No verbs in URL paths; collections use plural nouns; HTTP methods match semantics table (POST→201+Location, DELETE→204, etc.); versioning present on all endpoints; no breaking changes without version bump
