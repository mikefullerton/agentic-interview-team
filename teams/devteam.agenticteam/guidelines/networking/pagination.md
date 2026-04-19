---

id: 49acdf9f-e4cb-4492-a620-809438eefb37
title: "Pagination"
domain: agentic-cookbook://guidelines/implementing/networking/pagination
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Prefer **cursor pagination** for most APIs — stable under concurrent mutations, consistent"
platforms: []
tags: 
  - networking
  - pagination
depends-on: []
related: []
references: 
  - https://google.aip.dev/158
  - https://opensource.zalando.com/restful-api-guidelines/#pagination
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - api-integration
  - data-modeling
---

# Pagination

**Cursor pagination** SHOULD be preferred for most APIs — stable under concurrent mutations, consistent
performance at any depth. Use offset pagination only when users need page numbers or data
is relatively static.

**Cursor response:**
```json
{
  "data": [ ... ],
  "pagination": {
    "next_cursor": "eyJpZCI6MTAwfQ==",
    "has_more": true
  }
}
```

**Offset response:**
```json
{
  "data": [ ... ],
  "pagination": {
    "offset": 20,
    "limit": 10,
    "total": 142
  }
}
```

References:
- [Google AIP-158: Pagination](https://google.aip.dev/158)
- [Zalando: Pagination](https://opensource.zalando.com/restful-api-guidelines/#pagination)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
