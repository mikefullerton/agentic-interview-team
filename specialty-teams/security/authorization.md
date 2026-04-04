---
name: authorization
description: Deny by default, server-side enforcement only, least privilege scopes, RBAC, BOLA/IDOR prevention via resource ownership...
artifact: guidelines/security/authorization.md
version: 1.0.0
---

## Worker Focus
Deny by default, server-side enforcement only, least privilege scopes, RBAC, BOLA/IDOR prevention via resource ownership checks

## Verify
Every endpoint has explicit permission check; no resource returned without ownership verification; no client-side-only authorization gate
