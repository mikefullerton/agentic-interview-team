---
name: feature-flags
description: All features gated behind feature flags from initial implementation; `FeatureFlagProvider` interface (`isEnabled(key) ->...
artifact: guidelines/feature-management/feature-flags.md
version: 1.0.0
---

## Worker Focus
All features gated behind feature flags from initial implementation; `FeatureFlagProvider` interface (`isEnabled(key) -> Bool`) with local default (UserDefaults/SharedPreferences/localStorage/JSON config); DI-swappable backend implementation; flag keys documented in spec

## Verify
New features have a feature flag from day one; `FeatureFlagProvider` interface implemented with local default; no hardcoded feature enable/disable in business logic; flag keys listed in spec or documentation
