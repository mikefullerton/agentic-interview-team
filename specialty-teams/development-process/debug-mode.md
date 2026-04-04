---
name: debug-mode
description: Debug-only configuration panel not included in release builds — contains feature flag overrides, analytics event log, A/...
artifact: guidelines/feature-management/debug-mode.md
version: 1.0.0
---

## Worker Focus
Debug-only configuration panel not included in release builds — contains feature flag overrides, analytics event log, A/B test variant picker, environment info; access guarded by `#if DEBUG` (Apple/Windows), `BuildConfig.DEBUG` (Android), `NODE_ENV === 'development'` (web)

## Verify
Debug panel absent from release/production builds; build guard present on all debug panel entry points; panel includes feature flag overrides and variant picker
