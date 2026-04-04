---
name: cors
description: Never reflect Origin header; static allowlist of permitted origins; no wildcard with credentials; `Access-Control-Max-Ag...
artifact: guidelines/security/cors.md
version: 1.0.0
---

## Worker Focus
Never reflect Origin header; static allowlist of permitted origins; no wildcard with credentials; `Access-Control-Max-Age: 86400`; no `null` origin; anchored regex if dynamic matching required

## Verify
CORS config uses static allowlist or anchored regex; no `Access-Control-Allow-Origin: *` with credentials; preflight `Access-Control-Max-Age` set; `null` origin not in allowlist
