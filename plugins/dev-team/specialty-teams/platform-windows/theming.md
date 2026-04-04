---
name: theming
description: WinUI 3 tri-state theming — Light, Dark, High Contrast; set app-level theme via `Application.RequestedTheme`; always use...
artifact: guidelines/platform/windows/theming.md
version: 1.0.0
---

## Worker Focus
WinUI 3 tri-state theming — Light, Dark, High Contrast; set app-level theme via `Application.RequestedTheme`; always use `ThemeResource` (not `StaticResource`) for colors and brushes to enable runtime switching; use semantic color resources (`TextFillColorPrimary`, `CardBackgroundFillColorDefault`) not hex values; define custom theme-aware colors in `ResourceDictionary` with Default/Light/Dark dictionaries

## Verify
No hex color values in XAML; `ThemeResource` used exclusively for colors and brushes; app renders correctly in Light, Dark, and High Contrast modes; custom colors defined with theme dictionary variants
