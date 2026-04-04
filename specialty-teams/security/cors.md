---
name: cors
description: Explicit origin allowlist (never reflect Origin), no wildcard with credentials, Access-Control-Max-Age, anchored regex f...
artifact: guidelines/security/cors.md
version: 1.0.0
---

## Worker Focus
Explicit origin allowlist (never reflect Origin), no wildcard with credentials, Access-Control-Max-Age, anchored regex for dynamic matching

## Verify
No wildcard origin; allowlist is static or anchored; credentials not combined with *; preflight cache header present
