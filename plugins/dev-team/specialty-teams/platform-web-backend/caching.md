---
name: caching
description: Server sets correct Cache-Control — immutable for versioned assets, `private, max-age=N` for dynamic, `no-store` for sen...
artifact: guidelines/networking/caching.md
version: 1.0.0
---

## Worker Focus
Server sets correct Cache-Control — immutable for versioned assets, `private, max-age=N` for dynamic, `no-store` for sensitive/mutations; ETag/If-None-Match support; never cache credentials or PII

## Verify
Sensitive endpoints have `Cache-Control: no-store`; versioned static assets have `max-age=31536000, immutable`; ETag header set on cacheable responses; mutations do not have a positive max-age
