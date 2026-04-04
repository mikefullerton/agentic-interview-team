---
name: content-security-policy
description: Implement `default-src 'none'` baseline, nonce-based script-src with strict-dynamic, no `unsafe-inline`/`unsafe-eval`, `...
artifact: guidelines/security/content-security-policy.md
version: 1.0.0
---

## Worker Focus
Implement `default-src 'none'` baseline, nonce-based script-src with strict-dynamic, no `unsafe-inline`/`unsafe-eval`, `frame-ancestors 'self'`; deploy in report-only mode first

## Verify
CSP header present; no `unsafe-inline` or `unsafe-eval` in script-src; nonce rotated per request; `frame-ancestors 'self'` set; no third-party domain in script-src without justification
