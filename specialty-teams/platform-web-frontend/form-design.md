---
name: form-design
description: Single-column layout, `<label>` top-aligned or floating, blur-event validation (not input-event), submit-event full vali...
artifact: guidelines/ui/form-design.md
version: 1.0.0
---

## Worker Focus
Single-column layout, `<label>` top-aligned or floating, blur-event validation (not input-event), submit-event full validation, inline error messages below field using ARIA (`aria-describedby`), pre-fill defaults, mark optional not required

## Verify
Validation triggered on blur not input; errors rendered inline below field; errors include icon + text (not color alone); `aria-describedby` links field to error; placeholder is not sole label
