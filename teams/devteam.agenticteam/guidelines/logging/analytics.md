---

id: 17216748-46e9-4e92-af3a-f4deeb843a8d
title: "Analytics"
domain: agentic-cookbook://guidelines/implementing/observability/analytics
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "All significant user actions MUST be instrumented via an `AnalyticsProvider` interface (`track(event, properties)`). ..."
platforms: 
  - csharp
  - kotlin
  - swift
  - typescript
tags: 
  - analytics
  - logging
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - logging
  - ui-implementation
---

# Analytics

All significant user actions MUST be instrumented via an `AnalyticsProvider` interface (`track(event, properties)`). No direct coupling to any analytics backend. Provide a logging-only default; swap in a backend (Mixpanel, Amplitude, PostHog) later.

Each spec SHOULD define events in an **Analytics** section.

---

# Analytics

All significant user actions MUST be instrumented via an `AnalyticsProvider` interface (`track(event, properties)`). No direct coupling to any analytics backend. Provide a logging-only default; swap in a backend (Mixpanel, Amplitude, PostHog) later. Each spec SHOULD define events in an **Analytics** section.

## Swift

Protocol + `os.log`-backed implementation as the default.

## Kotlin

Interface + `Timber`-backed implementation as the default.

## TypeScript

TypeScript interface + `console`-backed implementation as the default.

## C#

Interface + `ILogger`-backed implementation as the default. Same pattern as other platforms: no direct coupling to any analytics backend.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
