---

id: 73b254b4-c611-434a-a9f4-67c8a7155576
title: "Touch & Click Targets"
domain: agentic-cookbook://guidelines/implementing/ui/touch-click-targets
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Interactive elements MUST be large enough to tap or click accurately. Defer to the platform"
platforms: 
  - ios
  - kotlin
  - typescript
  - web
  - windows
tags: 
  - touch-click-targets
  - ui
depends-on: []
related: 
  - agentic-cookbook://guidelines/accessibility/accessibility
references: 
  - https://developer.apple.com/design/human-interface-guidelines/accessibility#User-interaction
  - https://learn.microsoft.com/en-us/windows/apps/design/input/guidelines-for-targeting
  - https://m3.material.io/foundations/accessible-design/accessibility-basics
  - https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
  - accessibility
---

# Touch & Click Targets

Interactive elements MUST be large enough to tap or click accurately. Defer to the platform
HIG first — each prescribes its own minimum:

| Platform | Minimum Target | Recommended |
|----------|---------------|-------------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Apple (iOS) | 44x44 pt | 44x44 pt |
| Android (Material) | 48x48 dp | 48x48 dp |
| Windows (Fluent) | 32x32 epx | 40x40 epx |
| Web (WCAG AA) | 24x24 CSS px | 44x44 CSS px |

**Cross-platform default: 44x44** when no platform HIG applies.

- The visual element (icon, text) can be smaller than the touch target — pad the hit area
- There MUST be minimum **8px spacing** between adjacent targets to prevent mis-taps
- Inline text links in paragraphs are exempt from size minimums but should have sufficient
  line height for comfortable tapping

See agentic-cookbook://guidelines/accessibility/accessibility for full accessibility requirements.

References:
- [Apple HIG: Accessibility — User Interaction](https://developer.apple.com/design/human-interface-guidelines/accessibility#User-interaction)
- [Material Design: Accessibility Basics](https://m3.material.io/foundations/accessible-design/accessibility-basics)
- [Fluent Design: Targeting Guidelines](https://learn.microsoft.com/en-us/windows/apps/design/input/guidelines-for-targeting)
- [WCAG 2.5.8: Target Size Minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
