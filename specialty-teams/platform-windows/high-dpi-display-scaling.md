---
name: high-dpi-display-scaling
description: XAML layout uses effective pixels (epx) — scaling is automatic for XAML content; provide bitmap assets at multiple scale...
artifact: guidelines/platform/windows/high-dpi-display-scaling.md
version: 1.0.0
---

## Worker Focus
XAML layout uses effective pixels (epx) — scaling is automatic for XAML content; provide bitmap assets at multiple scales (.scale-100, .scale-125, .scale-150, .scale-200, .scale-400); for custom rendering (Win2D, Direct3D) query `XamlRoot.RasterizationScale` and listen for `RasterizationScaleChanged`; never hard-code pixel sizes in code-behind

## Verify
No hard-coded pixel sizes in code-behind; bitmap assets present at all required scale suffixes; custom rendering handlers subscribe to `RasterizationScaleChanged`; layout tested at 100%, 150%, and 200% DPI
