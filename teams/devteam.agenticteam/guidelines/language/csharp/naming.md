---

id: 34486fb8-8a0b-4538-a40a-13124155cd56
title: "Naming"
domain: agentic-cookbook://guidelines/implementing/code-quality/naming
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "- `PascalCase` for types, methods, properties, public fields, constants, namespaces"
platforms: []
languages:
  - csharp
tags: 
  - csharp
  - language
  - naming
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - code-review
  - new-module
---

# Naming

Use .NET's established casing conventions consistently: `PascalCase` for public symbols, `camelCase` for locals, and `_camelCase` for private fields.

- Types, methods, properties, public fields, constants, namespaces MUST use `PascalCase`
- Parameters and local variables MUST use `camelCase`
- Private instance fields MUST use `_camelCase` (underscore prefix)
- `I` prefix for interfaces (e.g., `IDisposable`)
- Async methods MUST have the `Async` suffix (e.g., `SaveAsync`)
- Constants MUST use `PascalCase`, not `SCREAMING_SNAKE_CASE`
- Use `var` when the type is apparent from the right side of the assignment

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
