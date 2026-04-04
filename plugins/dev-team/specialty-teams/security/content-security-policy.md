---
name: content-security-policy
description: default-src 'none' baseline, nonce-based script-src with strict-dynamic, never unsafe-inline or unsafe-eval, frame-ances...
artifact: guidelines/security/content-security-policy.md
version: 1.0.0
---

## Worker Focus
default-src 'none' baseline, nonce-based script-src with strict-dynamic, never unsafe-inline or unsafe-eval, frame-ancestors 'self', report-only deployment first

## Verify
CSP header present; no unsafe-inline/unsafe-eval in script-src; nonce rotation; frame-ancestors set
