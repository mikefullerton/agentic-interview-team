---
name: security-compliance
description: 12 compliance checks — secure-authentication (OAuth/PKCE), server-side-authorization, secure-storage, input-sanitization...
artifact: compliance/security.md
version: 1.0.0
---

## Worker Focus
12 compliance checks — secure-authentication (OAuth/PKCE), server-side-authorization, secure-storage, input-sanitization, secure-transport (TLS 1.2+), secure-log-output (no PII/tokens), token-lifecycle, dependency-scanning, security-headers, content-security-policy, cors-allowlist, security-testing

## Verify
Each check has status with evidence; no PII in logs confirmed; token expiry ≤15min verified; dependency scan in CI; all 7 security headers present
