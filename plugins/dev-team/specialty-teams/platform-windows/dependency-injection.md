---
name: dependency-injection
description: Constructor injection via `Microsoft.Extensions.DependencyInjection`; use interface types for dependencies (not concrete...
artifact: guidelines/language/csharp/dependency-injection.md
version: 1.0.0
---

## Worker Focus
Constructor injection via `Microsoft.Extensions.DependencyInjection`; use interface types for dependencies (not concrete types); `Transient` for stateless services, `Scoped` for per-request, `Singleton` for thread-safe shared state; no scoped service injected into singleton (captive dependency); use `IOptions<T>` / `IOptionsSnapshot<T>` for configuration; registrations in `Add*()` extension methods

## Verify
All dependencies injected via constructor with interface types; no captive dependencies (scoped in singleton); `IOptions<T>` used for configuration binding; service registrations in extension methods
