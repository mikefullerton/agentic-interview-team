---
name: caching
description: Immutable versioned assets use `Cache-Control: public, max-age=31536000, immutable`; sensitive data uses `no-store`; ETa...
artifact: guidelines/networking/caching.md
version: 1.0.0
---

## Worker Focus
Immutable versioned assets use `Cache-Control: public, max-age=31536000, immutable`; sensitive data uses `no-store`; ETag conditional requests for revalidation; client-side cache invalidated after mutations

## Verify
Versioned JS/CSS/images have immutable Cache-Control; auth/session responses have no-store; ETag/If-None-Match flow implemented for dynamic content; mutations trigger cache invalidation
