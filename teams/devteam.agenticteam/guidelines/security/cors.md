---

id: 8ea0409f-405a-4f4d-9bbf-54bf21c86d33
title: "CORS"
domain: agentic-cookbook://guidelines/implementing/security/cors
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Cross-Origin Resource Sharing — get it right or don't enable it."
platforms: 
  - web
tags: 
  - cors
  - security
depends-on: []
related: []
references: 
  - https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
  - https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/07-Testing_Cross_Origin_Resource_Sharing
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - networking
  - security-review
  - api-integration
---

# CORS

Cross-Origin Resource Sharing — get it right or don't enable it.

- The Origin header MUST NOT be reflected back as `Access-Control-Allow-Origin`. Maintain an
  explicit allowlist of origins.
- `*` MUST NOT be used with credentials — browsers block this, and attempting it reveals a
  design misunderstanding.
- **Preflight caching:** SHOULD set `Access-Control-Max-Age: 86400` to reduce preflight overhead.
- **Minimize exposed headers:** Only what the client actually needs.

**Common misconfigurations:**
- Wildcard origin with credentials
- Regex matching without anchoring (`evil-example.com` matching `example.com`)
- Allowing `null` origin (exploitable via sandboxed iframes)
- Overly broad allowed methods and headers

References:
- [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [OWASP: CORS Testing](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/07-Testing_Cross_Origin_Resource_Sharing)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
