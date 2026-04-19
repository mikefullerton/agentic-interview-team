---

id: a7c2a089-7666-459e-b564-24cc30980936
title: "Visual Hierarchy"
domain: agentic-cookbook://guidelines/implementing/ui/visual-hierarchy
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Establish clear importance through size, weight, color, and spacing. Every screen should"
platforms: 
  - windows
tags: 
  - ui
  - visual-hierarchy
depends-on: []
related: 
  - agentic-cookbook://guidelines/accessibility/accessibility
references: 
  - https://developer.apple.com/design/human-interface-guidelines/layout
  - https://learn.microsoft.com/en-us/windows/apps/design/layout/
  - https://m3.material.io/foundations/layout/applying-layout/overview
  - https://www.nngroup.com/articles/visual-hierarchy-ux-definition/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
---

# Visual Hierarchy

Establish clear importance through size, weight, color, and spacing. Every screen should
have one obvious focal point — the primary action or content the user came for.

- **One primary action per screen** — there MUST be a single focal point; if everything is bold, nothing is bold
- Use size and weight (not just color) to distinguish heading levels
- Group related content with proximity; separate unrelated content with whitespace
- Interactive elements MUST be visually distinguishable from static content
- Disabled elements SHOULD be visually muted but still discoverable

See agentic-cookbook://guidelines/accessibility/accessibility for accessibility requirements (contrast, labels, focus order).

References:
- [NNGroup: Visual Hierarchy](https://www.nngroup.com/articles/visual-hierarchy-ux-definition/)
- [Apple HIG: Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Material Design: Applying Layout](https://m3.material.io/foundations/layout/applying-layout/overview)
- [Fluent Design: Layout](https://learn.microsoft.com/en-us/windows/apps/design/layout/)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
