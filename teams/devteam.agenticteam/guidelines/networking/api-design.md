---

id: 49399746-a81f-4163-8b07-0cfa11d87c2e
title: "API Design"
domain: agentic-cookbook://guidelines/implementing/networking/api-design
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Use REST with consistent conventions. Follow the platform API guidelines (Microsoft, Google,"
platforms: []
tags: 
  - api-design
  - networking
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - api-integration
  - new-module
---

# API Design

Use REST with consistent conventions. Follow the platform API guidelines (Microsoft, Google,
Zalando) for details — the essentials below are consensus across all three.

**URL conventions:**
- URLs MUST be lowercase with hyphens: `/order-items` not `/orderItems`
- Collections MUST use plural nouns: `/users`, `/orders`
- Nesting SHOULD be shallow (max 2 levels): `/users/{id}/orders`
- URLs MUST NOT contain verbs — the HTTP method is the verb
- Trailing slashes MUST NOT be used
- Query params for filtering/sorting: `/users?status=active&sort=-created_at`

**HTTP methods:**

| Method | Semantics | Idempotent | Success Code |
|--------|-----------|------------|-------------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| GET | Read | Yes | 200 |
| POST | Create | No | 201 + Location |
| PUT | Full replace | Yes | 200 |
| PATCH | Partial update | No | 200 |
| DELETE | Remove | Yes | 204 (no body) |

**Status codes — use the right one:**
- **200** OK — **201** Created — **204** No Content — **202** Accepted (async)
- **400** Bad Request — **401** Unauthorized — **403** Forbidden — **404** Not Found
- **409** Conflict — **422** Unprocessable Entity — **429** Too Many Requests
- **500** Internal Server Error — **503** Service Unavailable

**Versioning:** URL path versioning (`/v1/users`). Simple, explicit, industry consensus. Bump
major version only for breaking changes.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
