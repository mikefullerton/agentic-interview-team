---

id: e547d962-d561-4bd9-bb5a-50bdeec98335
title: "Color"
domain: agentic-cookbook://guidelines/implementing/ui/color
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Use color with intention — never as the sole means of conveying information."
platforms: 
  - typescript
  - web
  - windows
tags: 
  - color
  - ui
depends-on: []
related: 
  - agentic-cookbook://guidelines/accessibility/accessibility
references: 
  - https://developer.apple.com/design/human-interface-guidelines/color
  - https://learn.microsoft.com/en-us/windows/apps/design/style/color
  - https://m3.material.io/styles/color/system/how-the-system-works
  - https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html
  - https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
---

# Color

Use color with intention — never as the sole means of conveying information.

- **Semantic color tokens** — platforms' semantic colors SHOULD be used (e.g., `TextFillColorPrimary`,
  `label`, `onSurface`) rather than hard-coded hex values. They adapt to theme and accessibility
  settings automatically.
- **Limit the palette** — 1 primary/accent color, 1-2 neutral tones, plus semantic colors for
  success/warning/error. Avoid rainbow UIs.
- **Not color alone** — color MUST be paired with a secondary indicator (icon, shape, text, pattern)
  for state changes, errors, and status.
- **Contrast minimums** (WCAG AA, per agentic-cookbook://guidelines/accessibility/accessibility):

| Element | AA Minimum | AAA Enhanced |
|---------|-----------|-------------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Normal text (<18pt / <14pt bold) | 4.5:1 | 7:1 |
| Large text (18pt+ or 14pt+ bold) | 3:1 | 4.5:1 |
| Non-text UI components | 3:1 | — |

- **Dark mode** — every color MUST work in both light and dark themes. Test both.

References:
- [WCAG 1.4.3: Contrast Minimum](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [WCAG 1.4.11: Non-text Contrast](https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html)
- [Apple HIG: Color](https://developer.apple.com/design/human-interface-guidelines/color)
- [Material Design: Color System](https://m3.material.io/styles/color/system/how-the-system-works)
- [Fluent Design: Color](https://learn.microsoft.com/en-us/windows/apps/design/style/color)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
