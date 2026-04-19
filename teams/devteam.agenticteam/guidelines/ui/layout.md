---

id: 26c8e7d6-dde3-48d0-bde0-8a71a51a6674
title: "Layout"
domain: agentic-cookbook://guidelines/implementing/ui/layout
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Design for the content, not a fixed screen size. Layouts should adapt gracefully from"
platforms: 
  - typescript
  - web
  - windows
tags: 
  - layout
  - ui
depends-on: []
related: []
references: 
  - https://developer.apple.com/design/human-interface-guidelines/layout
  - https://learn.microsoft.com/en-us/windows/apps/design/layout/responsive-design
  - https://m3.material.io/foundations/layout/applying-layout/overview
  - https://www.nngroup.com/articles/mobile-first-not-mobile-only/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
---

# Layout

Design for the content, not a fixed screen size. Layouts should adapt gracefully from
compact to expanded contexts.

- **Single-column by default** — multi-column only when content density justifies it and
  screen width supports it
- **Content-first** — decide what information the user needs, then choose a layout. Don't
  start with a grid and fill it.
- **Consistent alignment** — pick a leading edge and stick to it. Mixed alignment creates
  visual noise.
- **Responsive breakpoints** — the platform's adaptive layout system (Size Classes,
  Window Size Classes, CSS media queries, VisualStateManager) MUST be used rather than hard-coded widths
- **Content density** — generous whitespace SHOULD be preferred for consumer UIs, allow denser layouts
  for productivity/data-heavy tools. Readability MUST NOT be sacrificed for density.
- **Scroll direction** — one primary scroll direction per view. Nested same-direction
  scrolling SHOULD be avoided.

References:
- [Apple HIG: Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Material Design: Adaptive Layout](https://m3.material.io/foundations/layout/applying-layout/overview)
- [Fluent Design: Responsive Design](https://learn.microsoft.com/en-us/windows/apps/design/layout/responsive-design)
- [NNGroup: Mobile-First Is Not Mobile-Only](https://www.nngroup.com/articles/mobile-first-not-mobile-only/)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
