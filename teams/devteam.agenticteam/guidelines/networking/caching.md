---

id: 3416a359-e01c-40b2-8876-4a8634d4395e
title: "Caching"
domain: agentic-cookbook://guidelines/implementing/networking/caching
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Use HTTP caching headers. The server controls cache policy; the client honors it."
platforms: 
  - typescript
  - web
tags: 
  - caching
  - networking
depends-on: []
related: []
references: 
  - https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
  - https://web.dev/articles/http-cache
  - https://www.rfc-editor.org/rfc/rfc9111
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - networking
  - performance-optimization
---

# Caching

Use HTTP caching headers. The server controls cache policy; the client honors it.

**Immutable assets** (versioned JS/CSS/images):
```
Cache-Control: public, max-age=31536000, immutable
```

**Dynamic but cacheable** (API responses):
```
Cache-Control: private, max-age=60
```

**MUST NOT cache** (sensitive data, mutations):
```
Cache-Control: no-store
```

**Conditional requests** — use ETags to avoid re-downloading unchanged data:
1. Server sends `ETag: "abc123"`
2. Client revalidates with `If-None-Match: "abc123"`
3. Server responds 304 Not Modified (no body) or 200 with new data

**Client-side invalidation:**
- After mutations (POST/PUT/DELETE), related cache entries MUST be invalidated
- Stale-while-revalidate: serve cached data immediately, refresh in background
- Framework support: React Query, SWR, Apollo Client all handle this natively

References:
- [RFC 9111: HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111)
- [web.dev: HTTP Cache](https://web.dev/articles/http-cache)
- [MDN: Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
