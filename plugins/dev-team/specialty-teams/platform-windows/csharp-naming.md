---
name: csharp-naming
description: PascalCase for types, methods, properties, public fields, constants, namespaces; camelCase for parameters and local vari...
artifact: guidelines/language/csharp/naming.md
version: 1.0.0
---

## Worker Focus
PascalCase for types, methods, properties, public fields, constants, namespaces; camelCase for parameters and local variables; `_camelCase` (underscore prefix) for private instance fields; `I` prefix for interfaces; `Async` suffix for async methods; constants use PascalCase not SCREAMING_SNAKE_CASE; use `var` when type is apparent

## Verify
Private fields use `_camelCase`; interfaces prefixed with `I`; async methods suffixed with `Async`; no `SCREAMING_SNAKE_CASE` constants; consistent PascalCase on public members
