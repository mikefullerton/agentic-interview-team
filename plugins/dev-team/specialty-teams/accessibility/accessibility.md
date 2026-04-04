---
name: accessibility
description: Semantic roles and labels on all interactive elements; full screen reader support (VoiceOver, TalkBack, Narrator, ARIA);...
artifact: guidelines/accessibility/accessibility.md
version: 1.0.0
---

## Worker Focus
Semantic roles and labels on all interactive elements; full screen reader support (VoiceOver, TalkBack, Narrator, ARIA); keyboard and switch control navigation; Dynamic Type/font scaling without layout breakage; WCAG AA contrast (4.5:1 text, 3:1 large text); meaningful focus order; platform accessibility display settings (reduced motion, high contrast, color inversion, bold text, grayscale)

## Verify
Every interactive element has a semantic role and accessible label; layouts tested at 2x font scale without clipping or overflow; contrast ratios verified at 4.5:1 for normal text; `prefers-reduced-motion` / `accessibilityReduceMotion` honored; platform-specific APIs used (SwiftUI environment keys, Android `AccessibilityManager`, ARIA roles + `aria-live`, Windows `AutomationProperties`)
