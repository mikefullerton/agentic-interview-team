---
name: pagination-client
description: Client handles cursor-based pagination (`next_cursor`, `has_more`) and offset-based; infinite scroll or "Load more" for ...
artifact: guidelines/networking/pagination.md
version: 1.0.0
---

## Worker Focus
Client handles cursor-based pagination (`next_cursor`, `has_more`) and offset-based; infinite scroll or "Load more" for cursor; page controls for offset; no full re-fetch on page change

## Verify
Pagination response shape parsed correctly; `has_more: false` hides load-more trigger; cursor stored and sent on next page request; loading state shown between pages
