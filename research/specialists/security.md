# Security Specialist

## Domain Coverage
Auth, transport security, token handling, input validation, secure storage, sensitive data, privacy, dependency security, CORS, CSP, user safety.

## Cookbook Sources
- `cookbook/guidelines/security/` (12+ guidelines)
- `cookbook/compliance/security-compliance.md`
- `cookbook/compliance/privacy-and-data.md`
- `cookbook/compliance/user-safety-compliance.md`

## Structured Questions

1. What authentication method are you planning — OAuth 2.0, passkeys, email/password, SAML, API keys? Will you support SSO? Different flows for different client types (native app, SPA, server-to-server)?

2. How long-lived will your access tokens be? Do you plan refresh token rotation? How will you handle absolute session timeouts?

3. How will you store tokens on each platform? HttpOnly cookies for web, Keychain for iOS, EncryptedSharedPreferences for Android? Are you avoiding localStorage?

4. How will you enforce authorization — endpoint level, resource level, or both? What's your plan for role-based access control? How will you prevent Broken Object Level Authorization (BOLA)?

5. What personal or sensitive data will your app collect? How are you classifying it by sensitivity tier? What field-level encryption strategy for the most sensitive data?

6. Are you planning server-side input validation using allowlists? Parameterized queries? How will you handle file uploads — MIME type validation, size limits, storage location?

7. What will error responses look like in production? Generic messages with correlation IDs, or will internal details leak through?

8. What's your logging strategy for sensitive operations? How will you ensure PII never appears in logs?

9. For web APIs, how will you configure CORS? Explicit origin allowlist or wildcard? What's your Content Security Policy strategy?

10. How will you manage third-party dependencies? Lockfiles? Automated vulnerability scanning in CI? Fail builds on critical/high vulnerabilities?

11. Will you enforce TLS 1.2+ (prefer 1.3)? HSTS? For mobile apps, certificate pinning with backup pins and a recovery plan?

12. Will your app send user data to external services? How will you disclose integrations and obtain consent?

13. What's your data retention policy? Which data fields are essential vs. nice-to-have? Can users export or delete their data?

## Exploratory Prompts

1. Why did you choose that authentication method? What tradeoffs did you consider?

2. What if you later needed GDPR or CCPA compliance? How would that change your data collection, consent flow, or retention? Could you restructure now to make that easier?

3. If a database breach happened, what would an attacker actually get? Which fields would be unencrypted? Walk me through the blast radius.

4. As you scale, how will you monitor for security anomalies — unusual token reuse, suspicious IP patterns, authorization failures?

5. If you integrated a new third-party service that needs user data, how would you govern that? What would you say "no" to?
