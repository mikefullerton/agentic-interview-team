---

id: 7b713210-43ee-4f7f-be9e-b096edb782ba
title: "Runtime Conditions"
domain: agentic-cookbook://guidelines/planning/code-quality/runtime-conditions
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Identify permissions, entitlements, environment checks, and configuration prerequisites that constrain when and where code can execute."
platforms:
  - csharp
  - ios
  - kotlin
  - typescript
  - web
  - windows
tags:
  - codebase-decomposition
depends-on: []
related: []
references: []
triggers:
  - code-review
  - new-module
---

# Runtime Conditions

Code does not execute in a vacuum. Some code requires the user to have granted a permission. Some code requires a specific OS version, a feature flag, an environment variable, or a configuration file. These runtime conditions are structural facts about a scope group — they determine the operational prerequisites and influence how the group must be tested, staged, and deployed. This lens catalogs every runtime condition the code depends on.

## Signals and Indicators

**Permission requests:**

- iOS/macOS: `requestWhenInUseAuthorization()` (location), `requestAccess(to:)` (contacts, calendar, photos), `AVCaptureDevice.requestAccess(for:)` (camera/microphone), `requestAuthorization()` (HealthKit, Motion), `UNUserNotificationCenter.requestAuthorization(options:)` (notifications)
- Android: `ActivityCompat.requestPermissions()` calls; manifest `<uses-permission>` declarations; runtime permission checks `ContextCompat.checkSelfPermission()`
- Web: `navigator.permissions.query()`, `navigator.geolocation.getCurrentPosition()`, `navigator.mediaDevices.getUserMedia()`, `Notification.requestPermission()`
- Windows: capability declarations in `Package.appxmanifest`; `DeviceAccessInformation` checks

**Entitlement declarations (iOS/macOS):**

- `.entitlements` file entries: `com.apple.security.network.client`, `com.apple.security.network.server`, `com.apple.developer.healthkit`, `com.apple.developer.icloud-container-identifiers`, `com.apple.developer.associated-domains`, `com.apple.security.app-sandbox`
- App Groups entitlement — code using shared containers requires this entitlement and implies coordination with an app extension

**Minimum OS version checks:**

- Swift: `if #available(iOS 16.0, *)`, `@available(iOS 16.0, *)`, `#unavailable`
- Kotlin/Android: `if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S)`, `@RequiresApi`
- C#/Windows: `ApiInformation.IsTypePresent()`, `Environment.OSVersion` comparisons
- Web: feature detection — `if ('serviceWorker' in navigator)`, `if (window.PaymentRequest)`, `CSS.supports()`

**Environment variable and configuration checks:**

- Direct `ProcessInfo.processInfo.environment["KEY"]` (Swift), `System.getenv("KEY")` (Java/Kotlin/C), `process.env.KEY` (Node.js), `Environment.GetEnvironmentVariable()` (C#)
- Configuration file loading: `.env` files, `appsettings.json`, `Info.plist` key reads (`Bundle.main.infoDictionary`), `AndroidManifest.xml` metadata reads
- Build-time conditionals: `#if DEBUG`, `#if FEATURE_X`, `BuildConfig.DEBUG` (Android), `#if os(iOS)`, conditional compilation flags

**Feature flag gates:**

- Remote config reads: `RemoteConfig.sharedInstance().configValue(forKey:)` (Firebase), `LaunchDarkly.shared.variation()`, `Unleash`, custom feature flag service calls
- A/B test enrollment checks
- Killswitch patterns — code guarded by `isFeatureEnabled` booleans fetched at startup

**Required configuration values:**

- API key reads that crash or return early if missing — these imply a configuration prerequisite
- Database connection string requirements
- OAuth client ID / redirect URI reads
- SSL certificate pinning configurations

## Boundary Detection

1. **Permission-gated code clusters.** Files that all request or check the same permission belong together — they share an operational prerequisite and a failure mode when the permission is denied.
2. **Entitlements define hard boundaries.** Code that requires an entitlement cannot run without it. If one candidate group requires an entitlement that others do not, they are distinct operational units.
3. **OS version gates mark optional feature envelopes.** Code behind `@available(iOS 16.0, *)` is conditionally executable — flag it as a version-gated feature within its scope group. If it constitutes a large portion of the group, it may warrant its own scope group.
4. **Environment-specific code belongs in a configuration scope group.** Code that reads environment variables, loads config files, or applies build-time conditionals is configuration infrastructure — it typically belongs in one scope group rather than scattered.
5. **Feature-flagged code is pre-production.** Large blocks of feature-flagged code indicate in-flight work. Document the flags but do not create scope groups around unenabled code paths.
6. **Remote config dependencies imply a network prerequisite.** Code that requires a remote config fetch before it can function has an implicit startup dependency — note this as an operational ordering constraint.

## Findings Format

```
RUNTIME CONDITIONS FINDINGS
============================

Permission Requirements:
  - <Permission> (<platform>) — requested in: <file list>
    Denial behavior: <what happens if denied — e.g., "feature disabled gracefully" | "hard crash" | "unclear">

Entitlements (iOS/macOS):
  - <entitlement key> — required by: <file list>

Minimum OS/Platform Version Gates:
  - <Version check> — files: <list>, guarded code: <brief description>

Environment/Configuration Prerequisites:
  - <Key or config file> — read in: <file list>, required vs optional: <required|optional>

Feature Flags:
  - <Flag name> (<system>) — guards: <file list or feature description>

Configuration Infrastructure Files:
  - <file> — purpose: <description>

Runtime Condition Anomalies:
  - <description — e.g., "Camera permission requested in 4 separate files with no centralized request handler">

Recommended Scope Group Candidates:
  - <Name> — <primary runtime condition>, <one-line rationale>
```

## Change History
