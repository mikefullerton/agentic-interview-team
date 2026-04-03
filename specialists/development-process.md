# Development Process & Product Specialist

## Role
Feature development cycle, iterative delivery, technical debt, feature flags, A/B testing, debug mode, small reversible decisions, YAGNI, prioritization.

## Persona
(coming)

## Cookbook Sources
- `principles/make-it-work-make-it-right-make-it-fast.md`
- `principles/small-reversible-decisions.md`
- `principles/yagni.md`
- `guidelines/feature-management/ab-testing.md`
- `guidelines/feature-management/debug-mode.md`
- `guidelines/feature-management/feature-flags.md`

## Specialty Teams

### make-it-work
- **Artifact**: `principles/make-it-work-make-it-right-make-it-fast.md`
- **Worker focus**: Sequential phases — correctness first (common case working), then refactor for clarity and edge cases, then optimize only what measurement proves is slow; never skip phase 2 to jump directly to performance optimization
- **Verify**: Code handles the common case correctly before refactoring; edge cases and error handling addressed in phase 2 before any performance work; performance optimizations are measurement-driven, not speculative

### small-reversible-decisions
- **Artifact**: `principles/small-reversible-decisions.md`
- **Worker focus**: Fast decisions on cheap-to-reverse choices; invest in understanding before committing to expensive-to-reverse decisions; incremental delivery over phased releases; binding decisions deferred to last responsible moment; architecture treated as continuous activity
- **Verify**: No large upfront architectural commitments without evidence; incremental delivery with feedback loops in place; reversibility considered when choosing between design options

### yagni
- **Artifact**: `principles/yagni.md`
- **Worker focus**: Build only for today's known requirements; no speculative abstractions, hooks for future features, or generalization beyond current need; cost of premature abstraction (ongoing maintenance) exceeds cost of adding it later when needed
- **Verify**: No unused abstraction layers, extension points, or generalization not required by current features; code complexity matches current requirements

### ab-testing
- **Artifact**: `guidelines/feature-management/ab-testing.md`
- **Worker focus**: Features that may need experimentation support variant assignment via `ExperimentProvider` interface (`variant(key) -> String`); local default implementation; debug panel override for manual variant selection
- **Verify**: Experimentable features implement `ExperimentProvider` interface; local default variant returns a valid value; debug panel allows variant override without code changes

### debug-mode
- **Artifact**: `guidelines/feature-management/debug-mode.md`
- **Worker focus**: Debug-only configuration panel not included in release builds — contains feature flag overrides, analytics event log, A/B test variant picker, environment info; access guarded by `#if DEBUG` (Apple/Windows), `BuildConfig.DEBUG` (Android), `NODE_ENV === 'development'` (web)
- **Verify**: Debug panel absent from release/production builds; build guard present on all debug panel entry points; panel includes feature flag overrides and variant picker

### feature-flags
- **Artifact**: `guidelines/feature-management/feature-flags.md`
- **Worker focus**: All features gated behind feature flags from initial implementation; `FeatureFlagProvider` interface (`isEnabled(key) -> Bool`) with local default (UserDefaults/SharedPreferences/localStorage/JSON config); DI-swappable backend implementation; flag keys documented in spec
- **Verify**: New features have a feature flag from day one; `FeatureFlagProvider` interface implemented with local default; no hardcoded feature enable/disable in business logic; flag keys listed in spec or documentation

## Exploratory Prompts

1. What if you had to ship something every week? How would that change planning, design, and verification?

2. Why are reversible decisions so valuable early on? What does that tell you about which risks to focus on?

3. If a feature flag stayed 6 months, would that be a problem? What's the cost of dead code paths?

4. What's the relationship between small decisions and learning velocity?
