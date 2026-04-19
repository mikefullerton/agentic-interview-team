---

id: 3741ed5e-0b67-48f2-b227-36ae152c0f4b
title: "Platform Design Languages"
domain: agentic-cookbook://guidelines/implementing/ui/platform-design-languages
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Defer to these canonical sources before applying the defaults in this file:"
platforms: 
  - kotlin
  - web
  - windows
tags: 
  - platform-design-languages
  - ui
depends-on: []
related: []
references: 
  - https://developer.apple.com/design/human-interface-guidelines/
  - https://fluent2.microsoft.design/
  - https://m3.material.io/
  - https://www.w3.org/TR/WCAG21/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
  - platform-integration
---

# Platform Design Languages

Defer to these canonical sources before applying the defaults in this file:

- **Apple**: [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- **Android**: [Material Design 3](https://m3.material.io/)
- **Windows**: [Fluent 2 Design System](https://fluent2.microsoft.design/)
- **Web**: [WCAG 2.1](https://www.w3.org/TR/WCAG21/) + platform-appropriate system

When the platform HIG prescribes a specific value (spacing, type size, target size),
the platform value MUST be used. Use the defaults below to fill gaps or establish a cross-platform
baseline.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
