---
name: analytics
description: All significant user actions instrumented via an `AnalyticsProvider` interface (`track(event, properties)`); no direct c...
artifact: guidelines/logging/analytics.md
version: 1.0.0
---

## Worker Focus
All significant user actions instrumented via an `AnalyticsProvider` interface (`track(event, properties)`); no direct coupling to any analytics backend; provide a logging-only default implementation; each spec defines events in an Analytics section

## Verify
`AnalyticsProvider` interface (not a concrete backend) used at call sites; logging-only default implementation present; no direct Mixpanel/Amplitude/PostHog imports in business logic; events documented in spec
