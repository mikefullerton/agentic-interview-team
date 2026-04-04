---
name: cors
description: Explicit static allowlist of origins, never reflect Origin, no wildcard with credentials, `Access-Control-Max-Age: 86400...
artifact: guidelines/security/cors.md
version: 1.0.0
---

## Worker Focus
Explicit static allowlist of origins, never reflect Origin, no wildcard with credentials, `Access-Control-Max-Age: 86400`, no `null` origin, anchored regex for any dynamic matching

## Verify
CORS config is a static list or anchored regex; no `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`; `null` not in allowlist; preflight Max-Age set
