---
name: pagination
description: Cursor pagination preferred for most APIs — stable under concurrent mutations, consistent performance at any depth; offs...
artifact: guidelines/networking/pagination.md
version: 1.0.0
---

## Worker Focus
Cursor pagination preferred for most APIs — stable under concurrent mutations, consistent performance at any depth; offset pagination only when users need page numbers or data is static; response includes `next_cursor` + `has_more` (cursor) or `offset`/`limit`/`total` (offset)

## Verify
All collection endpoints return paginated responses (not unbounded lists); cursor-based pagination used unless offset explicitly justified; pagination envelope present with `has_more` or `total`
