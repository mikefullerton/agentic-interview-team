---

id: e446ee3e-b8f2-40e7-b93d-3113e6a95e5d
title: "Debug mode"
domain: agentic-cookbook://guidelines/implementing/feature-management/debug-mode
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Apps MUST include a debug-only configuration panel (not in release builds):"
platforms: 
  - ios
  - kotlin
  - macos
  - typescript
  - web
  - windows
tags: 
  - debug-mode
  - feature-management
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - feature-flags
  - logging
---

# Debug mode

Apps MUST include a debug-only configuration panel (not in release builds):

- Feature flag overrides
- Analytics event log
- A/B test variant picker
- Environment info (version, build, OS, device)

Access methods:
- **Apple (iOS)**: Shake gesture, guarded by `#if DEBUG`
- **Apple (macOS)**: Debug menu item, guarded by `#if DEBUG`
- **Android**: Shake gesture, guarded by `BuildConfig.DEBUG`
- **Web**: `/debug` route, guarded by `NODE_ENV === 'development'`
- **Windows**: Debug-only settings page, guarded by `#if DEBUG`

---

# Debug Mode

Apps MUST include a debug-only configuration panel (not in release builds) with:

- Feature flag overrides
- Analytics event log
- A/B test variant picker
- Environment info (version, build, OS, device)

## TypeScript

Access via `/debug` route or keyboard shortcut (`Ctrl+Shift+D`), guarded by `process.env.NODE_ENV === 'development'`.

## Windows

Dev-only settings page guarded by `#if DEBUG`:

- Feature flag overrides
- Analytics event log
- Environment info (app version, OS version, device)
- Access via navigation menu item visible only in debug builds

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
