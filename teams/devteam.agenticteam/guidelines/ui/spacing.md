---

id: 536c1e46-36f9-4a44-b8f4-c9e4db94cf53
title: "Spacing"
domain: agentic-cookbook://guidelines/implementing/ui/spacing
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Use a consistent spatial scale based on a **4px base unit** (8px primary grid). All spacing,"
platforms: 
  - windows
tags: 
  - spacing
  - ui
depends-on: []
related: []
references: 
  - https://developer.apple.com/design/human-interface-guidelines/layout
  - https://learn.microsoft.com/en-us/windows/apps/design/layout/
  - https://m3.material.io/foundations/layout/overview
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
---

# Spacing

Use a consistent spatial scale based on a **4px base unit** (8px primary grid). All spacing,
padding, and margin values MUST be multiples of 4. This aligns with Apple HIG, Material
Design, and Fluent Design.

Default spacing scale: **4, 8, 12, 16, 24, 32, 48, 64**

- **4px** — tight spacing within compact elements (icon-to-label, badge padding)
- **8px** — default inner padding, spacing between related items
- **12px** — padding within cards or list items
- **16px** — standard content padding from screen/container edges
- **24px** — separation between content groups
- **32-64px** — major section separation

Arbitrary values (5px, 13px, 37px) SHOULD be avoided. If a value isn't on the scale, reconsider.

References:
- [Apple HIG: Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Material Design: Layout](https://m3.material.io/foundations/layout/overview)
- [Fluent Design: Layout](https://learn.microsoft.com/en-us/windows/apps/design/layout/)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
