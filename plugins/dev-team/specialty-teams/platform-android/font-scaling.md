---
name: font-scaling
description: Layouts must not break at 2x font size; check `Configuration.fontScale` and test with large font settings enabled; use s...
artifact: guidelines/language/kotlin/font-scaling.md
version: 1.0.0
---

## Worker Focus
Layouts must not break at 2x font size; check `Configuration.fontScale` and test with large font settings enabled; use sp units for text, avoid fixed dp font sizes

## Verify
Text sizes specified in sp; layout tested at 2x font scale without truncation or overflow; no hardcoded dp font sizes; scrollable containers used where text may expand
