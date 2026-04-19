---

id: 2609037a-fb89-4b49-88b0-7e4295e5d6f6
title: "Authorization"
domain: agentic-cookbook://guidelines/implementing/security/authorization
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "**Server-side authorization is the only real authorization.** Client-side checks (hiding"
platforms: 
  - typescript
  - web
tags: 
  - authorization
  - security
depends-on: []
related: []
references: 
  - https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html
  - https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - authentication
  - security-review
---

# Authorization

Enforce all access control server-side. Deny by default, grant least privilege, and verify object-level ownership on every request.

**Server-side authorization is the only real authorization.** Client-side checks (hiding
buttons, disabling fields) are UX conveniences — never security controls.

- **Deny by default** — if no explicit permission grants access, the request MUST be denied. Every new endpoint
  starts locked down.
- **Least privilege** — endpoints MUST request minimum scopes. Each endpoint enforces its own permission check.
- **RBAC** — define roles with minimal permissions. Prefer fine-grained permissions composed
  into roles over monolithic role checks.
- **Broken Object Level Authorization (BOLA)** — the #1 API security risk (OWASP API Top 10).
  The server MUST verify the authenticated user has access to the specific resource ID requested.
  Never assume "if they know the ID, they have access."

References:
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP Access Control Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
