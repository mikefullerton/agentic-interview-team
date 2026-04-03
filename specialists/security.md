# Security Specialist

## Role
Auth, transport security, token handling, input validation, secure storage, sensitive data, privacy, dependency security, CORS, CSP, user safety.

## Persona
(coming)

## Cookbook Sources
- `guidelines/security/` (13 files)
- `compliance/security.md`
- `compliance/privacy-and-data.md`
- `compliance/user-safety.md`

## Specialty Teams

### authentication
- **Artifact**: `guidelines/security/authentication.md`
- **Worker focus**: OAuth 2.0/OIDC with PKCE for public clients, system browser for native apps, no implicit flow, SSO and multi-client strategies
- **Verify**: No implicit flow; PKCE code_challenge present; system browser on native (no embedded WebView); no client_secret in public clients

### authorization
- **Artifact**: `guidelines/security/authorization.md`
- **Worker focus**: Deny by default, server-side enforcement only, least privilege scopes, RBAC, BOLA/IDOR prevention via resource ownership checks
- **Verify**: Every endpoint has explicit permission check; no resource returned without ownership verification; no client-side-only authorization gate

### token-handling
- **Artifact**: `guidelines/security/token-handling.md`
- **Worker focus**: Access token lifetime 5-15min, no PII in JWT claims, refresh token rotation, platform-appropriate secure storage
- **Verify**: Access token exp ≤15min; JWT payload contains no PII; refresh rotation configured; storage uses Keychain/EncryptedSharedPreferences/HttpOnly cookie

### transport-security
- **Artifact**: `guidelines/security/transport-security.md`
- **Worker focus**: TLS 1.2 minimum (prefer 1.3), disable TLS 1.0/1.1, HSTS with max-age=31536000 includeSubDomains preload, certificate pinning only where truly needed
- **Verify**: TLS 1.0/1.1 disabled; HSTS header present with correct max-age; no HTTP-only endpoints; pinned certs have rotation plan if used

### cors
- **Artifact**: `guidelines/security/cors.md`
- **Worker focus**: Explicit origin allowlist (never reflect Origin), no wildcard with credentials, Access-Control-Max-Age, anchored regex for dynamic matching
- **Verify**: No wildcard origin; allowlist is static or anchored; credentials not combined with *; preflight cache header present

### content-security-policy
- **Artifact**: `guidelines/security/content-security-policy.md`
- **Worker focus**: default-src 'none' baseline, nonce-based script-src with strict-dynamic, never unsafe-inline or unsafe-eval, frame-ancestors 'self', report-only deployment first
- **Verify**: CSP header present; no unsafe-inline/unsafe-eval in script-src; nonce rotation; frame-ancestors set

### input-validation
- **Artifact**: `guidelines/security/input-validation.md`
- **Worker focus**: All validation duplicated server-side, allowlists over denylists, validate-sanitize-escape order, parameterized queries only, context-aware output encoding
- **Verify**: Server-side validation exists independent of client; parameterized queries used; output encoding is context-specific; no raw user input concatenated into queries/HTML

### sensitive-data
- **Artifact**: `guidelines/security/sensitive-data.md`
- **Worker focus**: Data minimization with explicit DTOs (not raw DB models), PII classification tiers, field-level encryption for SSN/payment via KMS, no PII/tokens/passwords in logs at any level
- **Verify**: API responses use explicit DTOs; highly sensitive fields encrypted at app layer; no PII or token values in log output; KMS used for SSN/payment

### secure-storage
- **Artifact**: `guidelines/security/secure-storage.md`
- **Worker focus**: Platform secure storage for all tokens/credentials/sensitive data — Keychain (Swift), EncryptedSharedPreferences (Kotlin), DPAPI (Windows), never plaintext config files
- **Verify**: No secrets in UserDefaults, SharedPreferences, plists, or app settings; correct platform API (Keychain/EncryptedSharedPreferences/DPAPI) used

### privacy
- **Artifact**: `guidelines/security/privacy.md`
- **Worker focus**: Collect only what's needed, prefer on-device processing, opt-in consent for non-essential collection, app functional on deny, data minimization
- **Verify**: No extraneous data fields collected; consent prompt present for non-essential data; fallback path when user denies; no plaintext token storage

### dependency-security
- **Artifact**: `guidelines/security/dependency-security.md`
- **Worker focus**: Lockfiles committed, CI audit step (npm audit/pip-audit/Dependabot) failing on critical/high, pinned versions (no wildcard), SRI on CDN assets
- **Verify**: Lockfile committed; audit step in CI config; no * version ranges; SRI integrity attributes on CDN script/style tags

### security-headers-checklist
- **Artifact**: `guidelines/security/security-headers-checklist.md`
- **Worker focus**: All 7 required headers on every web response — Strict-Transport-Security, Content-Security-Policy, X-Content-Type-Options nosniff, X-Frame-Options DENY, Referrer-Policy, Permissions-Policy, Cache-Control no-store on sensitive responses
- **Verify**: All 7 headers present in HTTP response; nosniff on content-type; Cache-Control no-store on responses containing credentials or PII

### security-compliance
- **Artifact**: `compliance/security.md`
- **Worker focus**: 7 compliance checks — secure-authentication, server-side-authorization, secure-storage, input-sanitization, secure-transport, secure-log-output, token-lifecycle
- **Verify**: Each compliance check has a status (passed/failed/partial/n-a) with evidence

### privacy-and-data-compliance
- **Artifact**: `compliance/privacy-and-data.md`
- **Worker focus**: 7 compliance checks — data-minimization, consent-before-collection, secure-data-storage, no-pii-in-logs, data-retention-policy, data-portability, third-party-disclosure
- **Verify**: Each compliance check has a status with evidence; retention policy explicitly stated

### user-safety-compliance
- **Artifact**: `compliance/user-safety.md`
- **Worker focus**: 6 compliance checks — content-moderation, age-appropriate-content, abuse-prevention, harmful-content-filtering, reporting-mechanism, safe-defaults
- **Verify**: Each compliance check has a status; safe-defaults confirmed (safety features on by default, not opt-in)

## Exploratory Prompts

1. If a data breach exposed your token store tomorrow, what's the blast radius? How many users? How quickly can you rotate? What's the forensic trail?
2. Walk me through the last time you added a new API endpoint. What security checklist did you follow? What got missed?
3. How do you handle a user who wants all their data deleted? Can you actually find and remove everything?
4. What happens when a dependency gets a CVE published against it on a Friday night? Who gets paged? How fast does the fix ship?
5. Your app goes viral in a country with strict data residency laws. What breaks?
