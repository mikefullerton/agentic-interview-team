---
name: color
description: CSS custom properties (not hard-coded hex), semantic color tokens per design system, WCAG AA contrast ratios, `prefers-c...
artifact: guidelines/ui/color.md
version: 1.0.0
---

## Worker Focus
CSS custom properties (not hard-coded hex), semantic color tokens per design system, WCAG AA contrast ratios, `prefers-color-scheme` dark mode support, color never sole state indicator

## Verify
No raw hex values in component styles; color contrast ≥4.5:1 text, ≥3:1 large text/UI; `prefers-color-scheme: dark` handled; state changes always include non-color indicator
