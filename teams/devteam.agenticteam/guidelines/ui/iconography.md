---

id: 98c5c5c2-5a45-4425-97b7-31932cb6af0c
title: "Iconography"
domain: agentic-cookbook://guidelines/implementing/ui/iconography
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Icons supplement text — they do not replace it (except for universally understood symbols"
platforms: 
  - windows
tags: 
  - iconography
  - ui
depends-on: []
related: []
references: 
  - https://developer.apple.com/design/human-interface-guidelines/sf-symbols
  - https://learn.microsoft.com/en-us/windows/apps/design/style/icons
  - https://m3.material.io/styles/icons/overview
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
---

# Iconography

Icons supplement text — they do not replace it (except for universally understood symbols
like play, pause, close, and search).

- The platform's native icon set SHOULD be used first (SF Symbols, Material Symbols, Segoe Fluent Icons)
- All icons accompanying actions MUST have a text label or accessible name
- Maintain consistent size and weight across the UI — don't mix outlined and filled styles
  without intention (e.g., filled = selected, outlined = unselected)
- Minimum icon size: 16x16pt for decorative, 24x24pt for interactive (see Touch & Click Targets
  for the full hit area)
- Icons conveying state (error, success, warning) MUST be paired with color AND shape —
  see Color section

References:
- [Apple HIG: SF Symbols](https://developer.apple.com/design/human-interface-guidelines/sf-symbols)
- [Material Design: Icons](https://m3.material.io/styles/icons/overview)
- [Fluent Design: Icons](https://learn.microsoft.com/en-us/windows/apps/design/style/icons)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
