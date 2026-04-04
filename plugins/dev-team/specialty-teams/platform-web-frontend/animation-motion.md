---
name: animation-motion
description: CSS transitions and JS animations use correct duration ranges per interaction type; `prefers-reduced-motion: reduce` med...
artifact: guidelines/ui/animation-motion.md
version: 1.0.0
---

## Worker Focus
CSS transitions and JS animations use correct duration ranges per interaction type; `prefers-reduced-motion: reduce` media query disables/simplifies all animations; no continuous loops or large-distance motion

## Verify
`prefers-reduced-motion` media query handled in CSS; no `animation: infinite` without reduced-motion fallback; transition durations within specified ranges for interaction type
