---

id: 2b9e9fbb-6df8-4dc2-b02d-3b97f6e434fb
title: "High DPI / Display Scaling"
domain: agentic-cookbook://guidelines/implementing/ui/high-dpi-display-scaling
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "XAML layout uses effective pixels (epx) — scaling is automatic for all XAML-rendered content."
platforms: 
  - csharp
  - windows
tags: 
  - high-dpi-display-scaling
  - platform
  - windows
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
  - accessibility
---

# High DPI / Display Scaling

XAML layout uses effective pixels (epx) — scaling is automatic for all XAML-rendered content.

- Bitmap assets MUST be provided at multiple scales: `.scale-100`, `.scale-125`, `.scale-150`, `.scale-200`, `.scale-400`
- For custom rendering (Win2D, Direct3D interop), query `XamlRoot.RasterizationScale` and listen for `RasterizationScaleChanged`
- Pixel sizes MUST NOT be hard-coded in code-behind — rely on XAML layout and the scaling system

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
