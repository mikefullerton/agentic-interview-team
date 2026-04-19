---

id: 22f1ca04-2d1d-4faf-8bf0-c6abcd60802c
title: "Sensitive Data"
domain: agentic-cookbook://guidelines/implementing/security/sensitive-data
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Minimize what you collect, encrypt what you keep, never log what you shouldn't."
platforms: 
  - typescript
  - web
tags: 
  - security
  - sensitive-data
depends-on: []
related: []
references: 
  - https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
  - https://csrc.nist.gov/publications/detail/sp/800-122/final
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - security-review
  - logging
---

# Sensitive Data

Minimize what you collect, encrypt what you keep, never log what you shouldn't.

- **Data minimization** — APIs MUST return only fields the client needs. Use explicit response DTOs,
  never dump database models directly.
- **PII classification** — data MUST be classified by sensitivity (public, internal, PII, sensitive PII).
  Apply controls proportional to tier.
- **Field-level encryption** — encrypt highly sensitive fields (SSN, payment info) at the
  application level with a KMS (AWS KMS, Azure Key Vault, GCP KMS). Separate from database-level
  encryption.
- **No PII in logs** — tokens, passwords, credit card numbers, or PII MUST NOT be logged. Mask/redact
  in all log outputs, including debug level. See agentic-cookbook://guidelines/security/privacy
- **No internals in API responses** — internal IDs, stack traces, or database
  error messages MUST NOT be exposed in production. Return generic errors with correlation IDs.
- **Cache-Control: no-store** on responses containing sensitive data.

References:
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [NIST SP 800-122: PII Guide](https://csrc.nist.gov/publications/detail/sp/800-122/final)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
