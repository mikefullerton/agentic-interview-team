---
name: token-handling
description: Access token lifetime 5-15min, no PII in JWT claims, refresh token rotation, platform-appropriate secure storage
artifact: guidelines/security/token-handling.md
version: 1.0.0
---

## Worker Focus
Access token lifetime 5-15min, no PII in JWT claims, refresh token rotation, platform-appropriate secure storage

## Verify
Access token exp ≤15min; JWT payload contains no PII; refresh rotation configured; storage uses Keychain/EncryptedSharedPreferences/HttpOnly cookie
