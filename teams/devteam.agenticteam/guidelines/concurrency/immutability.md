---

id: 50ea8b39-813d-4325-be31-0ae19b8a3baf
title: "Immutability"
domain: agentic-cookbook://guidelines/implementing/concurrency/immutability
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Mutable shared state is the root cause of most concurrency bugs. Default to immutable values; introduce mutability on..."
platforms: 
  - kotlin
  - typescript
tags: 
  - concurrency
  - immutability
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - concurrency
  - data-modeling
---

# Immutability

Mutable shared state is the root cause of most concurrency bugs. Immutable values MUST be the default; introduce mutability only where necessary. Value types SHOULD be preferred over reference types. Mutation MUST be contained behind clear boundaries.

## Kotlin

Use `val` by default. Use `data class` for value types. Introduce `var` only when mutation is required, and contain mutable state behind `StateFlow`.

## TypeScript

Use `const` by default. Use `var`/`let` only when mutation is required. Prefer `useState` (React) for contained mutable state.

## C#

Use `readonly` fields and `readonly struct` by default. Introduce mutability only when required.

- Prefer `System.Collections.Immutable` (`ImmutableList<T>`, `ImmutableDictionary<K,V>`) for shared collections
- Use `record` for DTOs, API responses, domain events, value objects
- Use `record struct` / `readonly record struct` for small immutable value types
- Prefer positional records (`record Person(string Name, int Age)`) for simple data carriers
- Use `init` setters and `required` keyword for mandatory properties
- Use `with` expressions for non-destructive mutation
- Contain mutable state behind `ObservableObject` (UI) or thread-safe wrappers
- Reserve `class` with mutable state for entities with identity semantics

```csharp
// Immutable DTO
public record OrderSummary(string OrderId, decimal Total, DateTime CreatedAt);

// Modified copy
var updated = order with { Total = 99.99m };

// Readonly value type
public readonly record struct Point(double X, double Y);
```

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
