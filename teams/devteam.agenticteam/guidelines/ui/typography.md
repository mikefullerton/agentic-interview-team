---

id: 1971d5c6-592d-4959-aa2c-33ea4ff17d0d
title: "Typography"
domain: agentic-cookbook://guidelines/implementing/ui/typography
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Use the platform's system font. Establish a type scale with clear roles — don't invent"
platforms: 
  - ios
  - kotlin
  - macos
  - typescript
  - web
  - windows
tags: 
  - typography
  - ui
depends-on: []
related: 
  - agentic-cookbook://guidelines/accessibility/accessibility
references: 
  - https://developer.apple.com/design/human-interface-guidelines/typography
  - https://learn.microsoft.com/en-us/windows/apps/design/style/typography
  - https://m3.material.io/styles/typography/type-scale-tokens
  - https://www.w3.org/WAI/WCAG21/Understanding/text-spacing.html
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
---

# Typography

The platform's system font MUST be used. Establish a type scale with clear roles — don't invent
sizes ad-hoc.

Platform system fonts:
- **Apple**: SF Pro (iOS/macOS), New York (serif alternative)
- **Android**: Roboto, or system default via Material type system
- **Windows**: Segoe UI Variable
- **Web**: System font stack (`system-ui, -apple-system, sans-serif`)

Defaults when no design system exists:
- **Body text**: 14-17pt (16px is the safest cross-platform default)
- **Minimum readable size**: 11-12pt for captions/labels, text MUST NOT be smaller
- **Line height**: 1.4x-1.5x font size for body text
- **Heading scale**: Use the platform's built-in type scale (Dynamic Type, Material type
  tokens, Fluent type ramp) rather than inventing sizes

General principles:
- Limit to 2-3 font weights per screen (regular, medium/semibold, bold)
- All-caps SHOULD be avoided for more than a few words — harms readability and screen reader experience
- Paragraph width: 45-75 characters for comfortable reading
- See agentic-cookbook://guidelines/accessibility/accessibility for Dynamic Type / font scaling requirements

References:
- [Apple HIG: Typography](https://developer.apple.com/design/human-interface-guidelines/typography)
- [Material Design: Type Scale](https://m3.material.io/styles/typography/type-scale-tokens)
- [Fluent Design: Typography](https://learn.microsoft.com/en-us/windows/apps/design/style/typography)
- [WCAG 1.4.12: Text Spacing](https://www.w3.org/WAI/WCAG21/Understanding/text-spacing.html)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
