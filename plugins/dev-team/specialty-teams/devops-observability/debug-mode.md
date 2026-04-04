---
name: debug-mode
description: Debug-only configuration panel (not in release builds) with feature flag overrides, analytics event log, A/B test varian...
artifact: guidelines/feature-management/debug-mode.md
version: 1.0.0
---

## Worker Focus
Debug-only configuration panel (not in release builds) with feature flag overrides, analytics event log, A/B test variant picker, and environment info (version, build, OS, device); access method appropriate to platform (shake gesture, debug menu, /debug route, keyboard shortcut); guarded by DEBUG compile flag or NODE_ENV check

## Verify
Debug panel absent from release/production builds; panel includes flag overrides, analytics log, variant picker, and environment info; access method matches platform convention; guard condition verified
