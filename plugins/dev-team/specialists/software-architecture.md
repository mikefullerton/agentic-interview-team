# Software Architecture Specialist

## Role
Composition, dependency injection, boundaries, separation of concerns, modularity, testability, optimize for change, open-source preference, concurrency.

## Persona
(coming)

## Cookbook Sources
- `principles/composition-over-inheritance.md`
- `principles/dependency-injection.md`
- `principles/manage-complexity-through-boundaries.md`
- `principles/separation-of-concerns.md`
- `principles/meta-principle-optimize-for-change.md`
- `principles/open-source-preference.md`
- `guidelines/concurrency/concurrency.md`
- `guidelines/concurrency/immutability.md`

## Specialty Teams

### composition-over-inheritance
- **Artifact**: `principles/composition-over-inheritance.md`
- **Worker focus**: Default to composing behaviors from small, focused pieces; use inheritance only for genuine "is-a" relationships and even then sparingly; prefer protocols/interfaces over base classes; wrap rather than subclass when extending behavior
- **Verify**: No inheritance hierarchies more than 1 level deep except for genuine is-a relationships; shared behavior achieved via protocol/interface composition not base classes; no subclassing to extend behavior where wrapping is possible

### dependency-injection
- **Artifact**: `principles/dependency-injection.md`
- **Worker focus**: Components receive dependencies from outside, not constructed internally; pass services via constructor/initializer parameters or protocol properties; use protocol/interface types not concrete types; avoid service locator pattern (hidden global lookup)
- **Verify**: No `new ConcreteService()` inside a component that uses it; dependencies declared as protocol/interface types in constructor signatures; no service locator or static factory lookups inside components; all dependencies injectable for testing

### manage-complexity-through-boundaries
- **Artifact**: `principles/manage-complexity-through-boundaries.md`
- **Worker focus**: Define ports (interfaces) describing what the application needs; use adapters to translate between external technologies and ports; test core application without databases, UIs, or networks; subsystems evolve independently behind their boundary
- **Verify**: Core business logic has no imports of UI, database, or network frameworks; adapters implement port interfaces; core can be unit-tested without infrastructure; at least one integration test verifies adapter-to-port wiring

### separation-of-concerns
- **Artifact**: `principles/separation-of-concerns.md`
- **Worker focus**: Each module has one reason to change; if describing what a module does requires "and," consider splitting; applies at every scale (functions, modules, services); presentation, domain, and data access are distinct layers
- **Verify**: No module that fetches and transforms and renders in the same class; UI layer contains no business logic; data layer contains no presentation logic; each module's purpose describable in a single clause without "and"

### optimize-for-change
- **Artifact**: `principles/meta-principle-optimize-for-change.md`
- **Worker focus**: Every architectural decision evaluated by whether it makes future change easier or harder; all other principles (composition, DI, boundaries, SoC) are strategies for reducing change cost; use this as the meta-question when tradeoffs arise
- **Verify**: Architectural decisions can be articulated in terms of change cost; no "easier now, harder later" shortcuts taken without explicit acknowledgment; key extension points (swappable backends, injectable services) present where change is anticipated

### open-source-preference
- **Artifact**: `principles/open-source-preference.md`
- **Worker focus**: When no native solution exists, research battle-tested open-source libraries and present options before building custom; custom implementation is a deliberate choice not a default; evaluate options on maintenance health, license, and fit
- **Verify**: Custom implementations of solved problems (parsers, serializers, HTTP clients, caches) are justified; open-source alternatives were evaluated; chosen library has an active maintenance history and compatible license

### concurrency
- **Artifact**: `guidelines/concurrency/concurrency.md`
- **Worker focus**: All lengthy work on background threads using platform async primitives (Swift Concurrency, Kotlin Coroutines, Promise/async, asyncio, async/await on .NET); never block the main/UI thread; show progress when UI is waiting on an async task; C# specifics: ConfigureAwait(false) in library code, no .Result/.Wait(), CancellationToken in all async APIs
- **Verify**: No synchronous I/O or network calls on main/UI thread; async/await used throughout (no .Result/.Wait() in C#); CancellationToken accepted by async APIs; progress shown in UI while awaiting background work

### concurrency-immutability
- **Artifact**: `guidelines/concurrency/immutability.md`
- **Worker focus**: Default to immutable values; introduce mutability only where necessary; prefer value types over reference types; contain mutation behind clear boundaries; Kotlin: val/data class/StateFlow; TypeScript: const/useState; C#: readonly/record/ImmutableList
- **Verify**: Shared data structures are immutable by default; mutable state contained behind StateFlow/ObservableObject/thread-safe wrappers; C# DTOs use record types; no mutable shared fields accessed from multiple concurrent contexts without synchronization

## Exploratory Prompts

1. If you had to rewrite your app but keep one module as-is, which would it be and why?

2. What if your business logic had to run in three environments — web, mobile, and a backend worker? How would that change your architecture?

3. If you discovered a bug in core business logic affecting thousands of users, how would you fix it with confidence?

4. Why does a particular piece of logic live where it does? What would it look like somewhere else?
