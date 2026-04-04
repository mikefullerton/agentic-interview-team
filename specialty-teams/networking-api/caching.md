---
name: caching
description: Server controls cache policy via headers; immutable versioned assets use `public, max-age=31536000, immutable`; dynamic ...
artifact: guidelines/networking/caching.md
version: 1.0.0
---

## Worker Focus
Server controls cache policy via headers; immutable versioned assets use `public, max-age=31536000, immutable`; dynamic API responses use `private, max-age=N`; sensitive/mutation responses use `no-store`; ETags for conditional requests; post-mutation cache invalidation

## Verify
Immutable assets have long-lived `Cache-Control: immutable`; sensitive responses have `Cache-Control: no-store`; `ETag` headers present on cacheable resources; mutations invalidate related cache entries
