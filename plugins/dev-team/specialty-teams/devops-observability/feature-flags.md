---
name: feature-flags
description: All features gated behind feature flags from initial implementation; `FeatureFlagProvider` interface (`isEnabled(key) ->...
artifact: guidelines/feature-management/feature-flags.md
version: 1.0.0
---

## Worker Focus
All features gated behind feature flags from initial implementation; `FeatureFlagProvider` interface (`isEnabled(key) -> Bool`); local default implementation (UserDefaults/SharedPreferences/localStorage/JSON config); swappable backend via DI; each spec lists flag keys in a Feature Flags section

## Verify
No feature code reachable without a flag check; `FeatureFlagProvider` interface (not a concrete store) used at call sites; flag keys documented in spec; local default implementation present and injectable
