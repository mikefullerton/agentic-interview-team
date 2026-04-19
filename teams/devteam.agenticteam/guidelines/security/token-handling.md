---

id: 2598f495-1820-47e7-b7e7-ce548d390148
title: "Token Handling"
domain: agentic-cookbook://guidelines/implementing/security/token-handling
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Short-lived (5-15 min). Include only necessary claims — no PII in JWTs"
platforms: 
  - kotlin
  - typescript
  - web
  - windows
tags: 
  - security
  - token-handling
depends-on: []
related: []
references: 
  - https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
  - https://datatracker.ietf.org/doc/html/rfc6750
  - https://datatracker.ietf.org/doc/html/rfc7519
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - authentication
  - security-review
---

# Token Handling

Keep access tokens short-lived (5-15 min), store refresh tokens in secure platform storage, and rotate them on every use.

### Access tokens

Short-lived (5-15 min). Include only necessary claims — no PII in JWTs
that transit untrusted parties.

### Refresh tokens

Longer-lived but bound to client. Use rotation (see Authentication above).
Store server-side when possible.

### Token refresh strategy

- Proactive refresh before expiry (e.g., at 75% of TTL)
- Queue concurrent requests during refresh to avoid race conditions
- Retry with backoff on refresh failure

### Secure storage per platform

See also agentic-cookbook://guidelines/security/privacy

- **Apple:** Keychain Services
- **Android:** EncryptedSharedPreferences / Android Keystore
- **Windows:** DPAPI (`ProtectedData`)
- **Web:** HttpOnly Secure SameSite cookies (never localStorage)

### Never do these

- Tokens MUST NOT be stored in `localStorage` or `sessionStorage` (XSS-accessible)
- Tokens MUST NOT be put in URL query parameters (logged in server logs, browser history, referrer headers)
- `alg: none` MUST NOT be used in JWTs — the `alg` header MUST be validated server-side against an allowlist
- Client-supplied JWT claims MUST NOT be trusted for authorization without server-side verification

References:
- [RFC 6750: Bearer Token Usage](https://datatracker.ietf.org/doc/html/rfc6750)
- [RFC 7519: JSON Web Tokens](https://datatracker.ietf.org/doc/html/rfc7519)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
