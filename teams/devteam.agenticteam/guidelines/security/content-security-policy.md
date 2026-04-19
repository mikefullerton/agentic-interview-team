---

id: 6f4cfd55-cb09-4ede-a53c-feaeb5781127
title: "Content Security Policy"
domain: agentic-cookbook://guidelines/implementing/security/content-security-policy
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Prevent XSS and injection with a strict CSP. Web apps only."
platforms: 
  - typescript
  - web
tags: 
  - content-security-policy
  - security
depends-on: []
related: []
references: 
  - https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html
  - https://csp-evaluator.withgoogle.com/
  - https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - security-review
  - ui-implementation
---

# Content Security Policy

Prevent XSS and injection with a strict CSP. Web apps only.

- **Start strict:** `default-src 'none'` then add only what is needed
- **Nonce-based scripts:** `script-src 'nonce-{random}' 'strict-dynamic'` SHOULD be used — more secure than
  domain allowlisting (bypassable via JSONP/CDN scripts)
- Policies MUST NOT include `'unsafe-inline'` or `'unsafe-eval'` for script-src
- **`frame-ancestors 'self'`** to prevent clickjacking (replaces X-Frame-Options)
- New policies SHOULD be deployed in report-only mode first (`Content-Security-Policy-Report-Only`) to find
  violations before enforcing

References:
- [MDN: CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [OWASP CSP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- [Google CSP Evaluator](https://csp-evaluator.withgoogle.com/)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
