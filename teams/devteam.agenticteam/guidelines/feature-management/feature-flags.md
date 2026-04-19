---

id: ac616d81-16c2-4f33-9ae4-139d5c24318d
title: "Feature flags"
domain: agentic-cookbook://guidelines/implementing/feature-management/feature-flags
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "All features MUST be gated behind feature flags from initial implementation. Define a `FeatureFlagProvider` interface..."
platforms: 
  - csharp
  - kotlin
  - swift
  - typescript
tags: 
  - feature-flags
  - feature-management
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - feature-flags
  - new-module
---

# Feature flags

All features MUST be gated behind feature flags from initial implementation. Define a `FeatureFlagProvider` interface (`isEnabled(key) -> Bool`), provide a local default implementation (UserDefaults/SharedPreferences/localStorage), swap in a backend implementation later via DI.

Each spec SHOULD list flag keys in a **Feature Flags** section.

---

# Feature Flags

All features MUST be gated behind feature flags from initial implementation. Define a `FeatureFlagProvider` interface (`isEnabled(key) -> Bool`), provide a local default implementation, and swap in a backend implementation later via dependency injection. Each spec SHOULD list flag keys in a **Feature Flags** section.

## Swift

Protocol + `UserDefaults`-backed implementation as the default.

## Kotlin

Interface + `SharedPreferences`-backed implementation as the default.

## TypeScript

TypeScript interface + `localStorage`-backed implementation as the default.

## C#

`IFeatureManager` interface + local JSON config as the default. Use the `Microsoft.FeatureManagement` NuGet package. Swap in Azure App Configuration for server-side flag evaluation later.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
