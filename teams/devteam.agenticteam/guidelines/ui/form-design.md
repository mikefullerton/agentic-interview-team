---

id: fdec6403-395b-4b98-b97d-b42e15cb77a6
title: "Form Design"
domain: agentic-cookbook://guidelines/implementing/ui/form-design
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Forms are where users do real work. Reduce friction at every step."
platforms: 
  - web
tags: 
  - form-design
  - ui
depends-on: []
related: []
references: 
  - https://developer.apple.com/design/human-interface-guidelines/text-fields
  - https://m3.material.io/components/text-fields/guidelines
  - https://www.nngroup.com/articles/errors-forms-design-guidelines/
  - https://www.nngroup.com/articles/web-form-design/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
  - input-handling
---

# Form Design

Forms are where users do real work. Reduce friction at every step.

###  Layout
- Single-column layout SHOULD be used — outperforms multi-column for completion rate
- Top-aligned or floating labels — fastest to scan and complete
- Group related fields visually with spacing or section headers
- Place primary action (Submit/Save) at the bottom, aligned with the form fields

###  Validation
- Validate on **blur** (when user leaves the field), not on every keystroke
- Validate the **full form on submit** as a final safety net
- Validation MUST NOT fire while the user is still actively typing in a field
- Success indicators (checkmarks) only for fields where the user genuinely wonders if
  input was accepted (e.g., username availability)

###  Error messages
- Errors MUST be shown **inline, directly below the field** — not only at the top of the form
- Use color + icon + text (never color alone)
- Be specific and actionable: "Password must be at least 8 characters" not "Invalid input"
- Don't blame the user

###  Other principles
- Use placeholder text for format hints, not as label replacement — placeholders disappear on focus
- Pre-fill and default where possible to reduce effort
- Mark optional fields, not required ones (most fields should be required; if they're not,
  reconsider asking)

References:
- [NNGroup: Form Design Guidelines](https://www.nngroup.com/articles/web-form-design/)
- [NNGroup: Error Messages in Forms](https://www.nngroup.com/articles/errors-forms-design-guidelines/)
- [Apple HIG: Text Fields](https://developer.apple.com/design/human-interface-guidelines/text-fields)
- [Material Design: Text Fields](https://m3.material.io/components/text-fields/guidelines)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
