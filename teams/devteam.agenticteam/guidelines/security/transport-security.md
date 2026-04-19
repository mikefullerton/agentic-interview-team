---

id: 5b026378-d418-406a-9aab-6e3f043901af
title: "Transport Security"
domain: agentic-cookbook://guidelines/implementing/security/transport-security
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "**TLS 1.2 minimum**, prefer TLS 1.3. Disable TLS 1.0 and 1.1 entirely."
platforms: 
  - typescript
  - web
tags: 
  - security
  - transport-security
depends-on: []
related: []
references: 
  - https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html
  - https://datatracker.ietf.org/doc/html/rfc8446
  - https://hstspreload.org/
  - https://wiki.mozilla.org/Security/Server_Side_TLS
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - networking
  - security-review
---

# Transport Security

Require TLS 1.2+ on every connection, enable HSTS on all production domains, and pin certificates for high-value mobile traffic.

**TLS 1.2 minimum** is REQUIRED, TLS 1.3 SHOULD be preferred. TLS 1.0 and 1.1 MUST be disabled entirely.

**HSTS:** Enable on all production domains:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```
Submit to the [HSTS preload list](https://hstspreload.org/).

**Certificate pinning — use with caution:**
- Pin to the intermediate CA, not the leaf (leaf certificates rotate)
- Acceptable for mobile apps; generally avoid for web (HPKP is deprecated)
- Backup pins MUST be included along with a recovery plan
- Consider Certificate Transparency monitoring as an alternative

**Cipher suites:** Use Mozilla's "Intermediate" or "Modern" TLS configuration. Prefer AEAD
ciphers (AES-GCM, ChaCha20-Poly1305).

References:
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html)
- [Mozilla Server Side TLS](https://wiki.mozilla.org/Security/Server_Side_TLS)
- [RFC 8446: TLS 1.3](https://datatracker.ietf.org/doc/html/rfc8446)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
