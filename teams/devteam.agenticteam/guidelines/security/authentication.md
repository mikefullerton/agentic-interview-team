---

id: aec38334-67fa-4c7e-bca2-607932af3f22
title: "Authentication"
domain: agentic-cookbook://guidelines/implementing/security/authentication
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Use OAuth 2.0 / OpenID Connect with PKCE for all public clients. The Implicit flow is"
platforms: 
  - csharp
  - ios
  - kotlin
  - typescript
  - web
  - windows
tags: 
  - authentication
  - security
depends-on: []
related: []
references: 
  - https://datatracker.ietf.org/doc/html/rfc7636
  - https://datatracker.ietf.org/doc/html/rfc8252
  - https://openid.net/specs/openid-connect-core-1_0.html
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - authentication
  - security-review
---

# Authentication

Use OAuth 2.0 / OpenID Connect with PKCE for all public clients. The Implicit flow is
deprecated — OAuth 2.1 removes it entirely.

**Per-platform auth flow:**
- **Native apps (iOS/Android/Windows):** Authorization Code + PKCE via the system browser
  (`ASWebAuthenticationSession`, Custom Tabs, `WebAuthenticationBroker`). Apps MUST NOT embed a
  WebView for auth — the app can intercept credentials.
- **SPAs:** Authorization Code + PKCE. Consider a Backend-for-Frontend (BFF) pattern where
  the SPA never handles tokens directly — the BFF holds tokens server-side in HttpOnly cookies.
- **Server-to-server:** Client Credentials flow.

**Session management:**
- Short-lived access tokens (5-15 minutes)
- Refresh token rotation MUST be used — each use issues a new refresh token and invalidates the old one.
  Detect reuse of a revoked refresh token and invalidate the entire token family.
- Absolute session timeouts server-side

References:
- [RFC 7636: PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [RFC 8252: OAuth for Native Apps](https://datatracker.ietf.org/doc/html/rfc8252)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
