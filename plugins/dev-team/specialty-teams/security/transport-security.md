---
name: transport-security
description: TLS 1.2 minimum (prefer 1.3), disable TLS 1.0/1.1, HSTS with max-age=31536000 includeSubDomains preload, certificate pin...
artifact: guidelines/security/transport-security.md
version: 1.0.0
---

## Worker Focus
TLS 1.2 minimum (prefer 1.3), disable TLS 1.0/1.1, HSTS with max-age=31536000 includeSubDomains preload, certificate pinning only where truly needed

## Verify
TLS 1.0/1.1 disabled; HSTS header present with correct max-age; no HTTP-only endpoints; pinned certs have rotation plan if used
