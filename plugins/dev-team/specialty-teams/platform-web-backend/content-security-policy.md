---
name: content-security-policy
description: Server sets CSP header on all HTML responses; `default-src 'none'` baseline; nonce-based `script-src` with `strict-dynam...
artifact: guidelines/security/content-security-policy.md
version: 1.0.0
---

## Worker Focus
Server sets CSP header on all HTML responses; `default-src 'none'` baseline; nonce-based `script-src` with `strict-dynamic`; no `unsafe-inline`/`unsafe-eval`; `frame-ancestors 'self'`; report-only mode first

## Verify
CSP header present on HTML responses; no `unsafe-inline` or `unsafe-eval` in script-src; nonce generated per-request; `frame-ancestors 'self'` present
