---
name: secure-storage
description: Platform secure storage for all tokens/credentials/sensitive data — Keychain (Swift), EncryptedSharedPreferences (Kotlin...
artifact: guidelines/security/secure-storage.md
version: 1.0.0
---

## Worker Focus
Platform secure storage for all tokens/credentials/sensitive data — Keychain (Swift), EncryptedSharedPreferences (Kotlin), DPAPI (Windows), never plaintext config files

## Verify
No secrets in UserDefaults, SharedPreferences, plists, or app settings; correct platform API (Keychain/EncryptedSharedPreferences/DPAPI) used
