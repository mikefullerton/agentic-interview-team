---

id: 4cb7c242-3ade-4d59-9c74-67c1d5f9c107
title: "RTL layout support"
domain: agentic-cookbook://guidelines/implementing/internationalization/rtl-support
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "All layouts MUST support right-to-left languages:"
platforms: 
  - csharp
  - kotlin
  - swift
  - typescript
  - web
  - windows
tags: 
  - internationalization
  - rtl-support
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - internationalization
  - ui-implementation
---

# RTL layout support

All layouts MUST support right-to-left languages:

1. Use **leading/trailing** (not left/right) for alignment and padding
2. Mirror icons with directional meaning (forward/back arrows)
3. Do NOT mirror non-directional icons (checkmarks, clocks)
4. Test with RTL locale enabled

Platform notes:
- **Apple**: Use `.environment(\.layoutDirection, .rightToLeft)` in previews. SwiftUI handles leading/trailing automatically.
- **Android**: Set `android:supportsRtl="true"`. Use `start`/`end` instead of `left`/`right`.
- **Web**: Use `dir="rtl"` attribute. Use CSS logical properties (`margin-inline-start` not `margin-left`).
- **Windows**: Use `FlowDirection` property. WinUI 3 XAML handles leading/trailing automatically.

---

# RTL Support

All layouts MUST support right-to-left languages. Use leading/trailing (not left/right) for alignment and padding. Mirror icons with directional meaning (forward/back arrows). Do NOT mirror non-directional icons (checkmarks, clocks). Test with an RTL locale enabled.

## Kotlin

Set `android:supportsRtl="true"` in the manifest. Use `start`/`end` instead of `left`/`right` in layouts. Force RTL in developer options for testing.

## TypeScript

Use CSS logical properties throughout:

- `margin-inline-start` instead of `margin-left`
- `padding-inline-end` instead of `padding-right`
- `inset-inline-start` instead of `left`

Set `dir="rtl"` attribute on the root element for RTL locales.

## Windows

- Set `FlowDirection="RightToLeft"` on the root element for RTL locales
- WinUI 3 XAML layout handles leading/trailing automatically when FlowDirection is set
- Mirror icons with directional meaning (forward/back arrows)
- Do NOT mirror non-directional icons (checkmarks, clocks)
- Test with RTL language packs installed

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
