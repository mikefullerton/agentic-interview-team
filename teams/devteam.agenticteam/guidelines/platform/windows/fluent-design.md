---

id: 376daf6c-f2bd-4a33-9ab4-2a2af140e725
title: "Fluent Design"
domain: agentic-cookbook://guidelines/implementing/ui/fluent-design
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Use built-in WinUI 3 controls — they implement Fluent 2 natively. Never custom-draw what a standard control can do."
platforms: 
  - csharp
  - windows
tags: 
  - fluent-design
  - platform
  - windows
depends-on: []
related: []
references: 
  - https://learn.microsoft.com/en-us/windows/apps/design/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
  - platform-integration
---

# Fluent Design

Use built-in WinUI 3 controls — they implement Fluent 2 natively. Applications MUST NOT custom-draw what a standard control can do.

- Typography: Segoe UI Variable
- Icons: Segoe Fluent Icons
- Applications MUST follow [Windows design guidance](https://learn.microsoft.com/en-us/windows/apps/design/) for layout, spacing, and navigation patterns

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
