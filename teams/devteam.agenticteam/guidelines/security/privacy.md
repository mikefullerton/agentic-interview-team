---

id: 29057cf0-a38b-4c35-8b8b-52e12bf54784
title: "Privacy and security by default"
domain: agentic-cookbook://guidelines/implementing/security/privacy
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Collect only what is needed. Prefer on-device processing."
platforms: 
  - kotlin
  - swift
  - typescript
tags: 
  - privacy
  - security
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - security-review
  - data-modeling
---

# Privacy and security by default

Collect only what you need, prefer on-device processing, and require opt-in for non-essential data. Store secrets in platform keystores, never in plaintext.

### Data minimization

Collect only what is needed. Prefer on-device processing.

### Consent

Opt-in for non-essential data collection. Honor "deny" gracefully — the app must remain functional.

### Secure storage

Tokens and credentials MUST use platform secure storage (Keychain, EncryptedSharedPreferences, DPAPI, HttpOnly cookies).

### No PII logging

Never log personally identifiable information, even at debug level.

### TLS only

All network communication MUST use HTTPS.

### Input sanitization

Sanitize all user input before display (prevent XSS, injection).

Each spec SHOULD include a **Privacy** section documenting data collected and how it is stored.

---

# Privacy

Privacy and security must be built in from day one. Collect only what is needed. Prefer on-device processing. Opt-in for non-essential data collection. Honor "deny" gracefully — the app must remain functional. No PII in logs, even at debug level. All network communication MUST use HTTPS.

## Swift

Support App Tracking Transparency, App Privacy Report, and Private Relay compatibility. Include `NS*UsageDescription` keys with human-readable explanations for all permission prompts.

## Kotlin

Respect scoped storage, support per-app language preferences, and honor permission denials gracefully. Show rationale dialogs before runtime permission requests.

## TypeScript

1. **Content Security Policy**: Configure CSP headers to restrict script sources and prevent XSS.
2. **HttpOnly cookies**: Use HttpOnly secure cookies for authentication tokens. Never store tokens in `localStorage`.
3. **Input sanitization**: Sanitize all user input before display to prevent XSS and injection.
4. **TLS only**: All network communication MUST use HTTPS.
5. Minimize third-party scripts. Respect the Do Not Track header.

## C#

- Declare only required capabilities in `Package.appxmanifest` — avoid `broadFileSystemAccess` unless essential
- Use DPAPI for local secret storage (see secure-storage.md)
- No PII in logs, even at debug level
- Respect user consent: app must remain functional if optional data collection is denied

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
