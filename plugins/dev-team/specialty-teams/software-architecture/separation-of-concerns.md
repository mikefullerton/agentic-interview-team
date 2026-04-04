---
name: separation-of-concerns
description: Each module has one reason to change; if describing what a module does requires "and," consider splitting; applies at ev...
artifact: principles/separation-of-concerns.md
version: 1.0.0
---

## Worker Focus
Each module has one reason to change; if describing what a module does requires "and," consider splitting; applies at every scale (functions, modules, services); presentation, domain, and data access are distinct layers

## Verify
No module that fetches and transforms and renders in the same class; UI layer contains no business logic; data layer contains no presentation logic; each module's purpose describable in a single clause without "and"
