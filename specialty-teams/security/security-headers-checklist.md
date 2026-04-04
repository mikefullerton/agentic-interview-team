---
name: security-headers-checklist
description: All 7 required headers on every web response — Strict-Transport-Security, Content-Security-Policy, X-Content-Type-Option...
artifact: guidelines/security/security-headers-checklist.md
version: 1.0.0
---

## Worker Focus
All 7 required headers on every web response — Strict-Transport-Security, Content-Security-Policy, X-Content-Type-Options nosniff, X-Frame-Options DENY, Referrer-Policy, Permissions-Policy, Cache-Control no-store on sensitive responses

## Verify
All 7 headers present in HTTP response; nosniff on content-type; Cache-Control no-store on responses containing credentials or PII
