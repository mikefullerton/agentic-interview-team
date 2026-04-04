---
name: pagination
description: Cursor pagination by default (`next_cursor`, `has_more`) for most APIs; offset (`offset`, `limit`, `total`) only when pa...
artifact: guidelines/networking/pagination.md
version: 1.0.0
---

## Worker Focus
Cursor pagination by default (`next_cursor`, `has_more`) for most APIs; offset (`offset`, `limit`, `total`) only when page numbers required or data is static; consistent response envelope

## Verify
All collection endpoints paginated; cursor response includes `next_cursor` and `has_more`; offset response includes `total`; no unbounded list endpoints returning all records
