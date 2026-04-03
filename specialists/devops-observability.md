# DevOps & Observability Specialist

## Role
Structured logging, analytics instrumentation, tight feedback loops, performance compliance, feature flags, A/B testing, debug mode.

## Persona
(coming)

## Cookbook Sources
- `guidelines/logging/analytics.md`
- `guidelines/logging/logging.md`
- `principles/tight-feedback-loops.md`
- `compliance/performance.md`
- `guidelines/feature-management/feature-flags.md`
- `guidelines/feature-management/ab-testing.md`
- `guidelines/feature-management/debug-mode.md`

## Specialty Teams

### analytics
- **Artifact**: `guidelines/logging/analytics.md`
- **Worker focus**: All significant user actions instrumented via an `AnalyticsProvider` interface (`track(event, properties)`); no direct coupling to any analytics backend; provide a logging-only default implementation; each spec defines events in an Analytics section
- **Verify**: `AnalyticsProvider` interface (not a concrete backend) used at call sites; logging-only default implementation present; no direct Mixpanel/Amplitude/PostHog imports in business logic; events documented in spec

### logging
- **Artifact**: `guidelines/logging/logging.md`
- **Worker focus**: Every component and flow instrumented with structured logging using platform best-in-class framework (os.log/Logger on Apple, Timber on Android, console/pino/winston on web, logging module on Python, ILogger<T> on .NET); debug level for flow instrumentation; log state transitions, user interactions, async start/completion/failure; never log PII at any level
- **Verify**: Every component has a logger instance; structured logging framework used (not raw print/console.log/NSLog); no PII in log output; async task lifecycle (start/complete/fail) logged; C# uses message templates not string interpolation

### tight-feedback-loops
- **Artifact**: `principles/tight-feedback-loops.md`
- **Worker focus**: Optimize test suite runtime so tests actually get run; deploy small changes frequently; get real user feedback early; automate everything between commit and production observation
- **Verify**: Test suite completes in a time developers will tolerate locally; CI pipeline automated end-to-end; no manual steps between commit and deploy; deploy frequency supports small changes

### performance-compliance
- **Artifact**: `compliance/performance.md`
- **Worker focus**: 8 compliance checks — main-thread-freedom, animation-frame-rate (60fps/16ms), lazy-loading, resource-efficiency, startup-impact, image-optimization, caching-strategy, progress-indication (operations >200ms)
- **Verify**: Each compliance check has a status (passed/failed/partial/n-a) with evidence; no blocking calls on main/UI thread; progress shown for operations exceeding 200ms; large collections use lazy loading or pagination

### feature-flags
- **Artifact**: `guidelines/feature-management/feature-flags.md`
- **Worker focus**: All features gated behind feature flags from initial implementation; `FeatureFlagProvider` interface (`isEnabled(key) -> Bool`); local default implementation (UserDefaults/SharedPreferences/localStorage/JSON config); swappable backend via DI; each spec lists flag keys in a Feature Flags section
- **Verify**: No feature code reachable without a flag check; `FeatureFlagProvider` interface (not a concrete store) used at call sites; flag keys documented in spec; local default implementation present and injectable

### ab-testing
- **Artifact**: `guidelines/feature-management/ab-testing.md`
- **Worker focus**: Features that may need experimentation support variant assignment via `ExperimentProvider` interface (`variant(key) -> String`); local default implementation with debug panel override
- **Verify**: `ExperimentProvider` interface used at call sites; debug panel can override variant assignment; no hardcoded variant strings in feature code; local default returns a deterministic variant

### debug-mode
- **Artifact**: `guidelines/feature-management/debug-mode.md`
- **Worker focus**: Debug-only configuration panel (not in release builds) with feature flag overrides, analytics event log, A/B test variant picker, and environment info (version, build, OS, device); access method appropriate to platform (shake gesture, debug menu, /debug route, keyboard shortcut); guarded by DEBUG compile flag or NODE_ENV check
- **Verify**: Debug panel absent from release/production builds; panel includes flag overrides, analytics log, variant picker, and environment info; access method matches platform convention; guard condition verified

## Exploratory Prompts

1. What if you could see every user interaction in real time (with permission)? How would that change your product understanding?

2. What's the gap between "what we measure" and "what we care about"? Metrics that don't matter? Things that matter but can't be measured?

3. If your feedback loop got 10x faster, what would you do differently?

4. What's the cost of a slow test run or slow deploy? How does that manifest in developer behavior?
