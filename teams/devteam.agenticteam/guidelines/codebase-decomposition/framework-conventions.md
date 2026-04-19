---

id: ef2d2757-132a-403b-8e98-bbeca9c42deb
title: "Framework Conventions"
domain: agentic-cookbook://guidelines/planning/code-quality/framework-conventions
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Identify the architectural patterns imposed by the chosen framework and use those conventional units as primary scope group candidates."
platforms:
  - csharp
  - ios
  - kotlin
  - typescript
  - web
  - windows
tags:
  - codebase-decomposition
depends-on: []
related: []
references: []
triggers:
  - new-module
  - code-review
---

# Framework Conventions

Frameworks impose structure. A Rails app has controllers, models, and views. An Angular app has modules, components, services, and guards. A SwiftUI app has Views, ViewModels, and Stores. These conventions are not arbitrary — framework authors designed them as the intended unit of composition. When a codebase follows framework conventions, those conventions are the strongest guide to scope group boundaries. When a codebase violates them, note the divergence — it signals either intentional architectural evolution or accumulated technical debt.

## Signals and Indicators

**iOS/macOS UIKit patterns:**

- `UIViewController` subclasses — each view controller is a distinct screen or screen region. Child view controllers and their parent form a container unit.
- `UIView` / `UICollectionViewCell` / `UITableViewCell` subclasses — reusable view components; large custom views are candidates for their own scope group
- Coordinator pattern — a `Coordinator` class that owns and routes between view controllers; each coordinator defines a user flow
- `UIViewControllerRepresentable` — bridging UIKit into SwiftUI; the representable and its UIKit component belong together

**iOS/macOS SwiftUI patterns:**

- `View` + `ViewModel` pairs — a `View` struct and its `@ObservableObject` or `@Observable` view model form the canonical SwiftUI unit
- `View` + `Store` (The Composable Architecture / TCA) — `Reducer`, `State`, `Action`, and the `View` that drives them are one architectural unit
- `EnvironmentKey` + `EnvironmentValues` extension — environment-injected dependencies; the key and its consumers form a loose unit
- Preview providers — `PreviewProvider` / `#Preview` files belong with the view they preview

**Android patterns:**

- `Activity` + `Fragment` pairs — an activity and the fragments it hosts form a screen unit
- MVVM: `ViewModel` + `Fragment`/`Activity` + data binding layout — the ViewModel, its observers, and the UI that consumes it form one unit
- MVI: `ViewModel` + `UiState` sealed class + `UiEvent` — state, events, and the ViewModel that processes them
- Repository pattern — `SomeRepository` interface + implementation; the repository abstracts data access for a feature domain
- Use case / interactor pattern — `GetSomethingUseCase` — single-responsibility business logic unit; groups of related use cases form a feature scope group

**Web / React patterns:**

- React component + hook — a custom `useSomething` hook and the component(s) that use it form a unit if the hook is not shared
- Context + Provider — a `SomeContext` and its `SomeProvider` belong together; the components that consume the context are in the same scope group if the context is narrow
- Next.js: `page.tsx` + `layout.tsx` + `loading.tsx` + `error.tsx` — all route segment files for a given route are one unit
- Redux slice — `somethingSlice.ts` containing `reducer`, `actions`, and `selectors` for one domain; the slice and its `thunk` files form one scope group
- React Query — a set of `useQuery`/`useMutation` hooks for the same API resource domain belong together

**Angular patterns:**

- `NgModule` — each module is a declared scope boundary; lazy-loaded modules are natural scope groups
- Component + Template + Styles — a `.component.ts`, `.component.html`, and `.component.scss` triplet is one unit
- Service — an `@Injectable` service scoped to a module or root; the service and the components it primarily serves
- Guard + Resolver — route guards and resolvers belong with the routes they protect/resolve
- Interceptor — HTTP interceptors are cross-cutting infrastructure (see `cross-cutting-detection`)

**C# / ASP.NET patterns:**

- Controller + ViewModel — an `*Controller.cs` and its associated `*ViewModel.cs` request/response types form one unit
- Repository + Entity — a `SomeRepository.cs` and its `SomeEntity.cs` / `SomeDbContext.cs` form a persistence unit
- MediatR: `Query`/`Command` + `Handler` — the request type and its handler are one unit; group by feature domain
- Blazor: `.razor` component + `.razor.cs` code-behind — one unit

**Plugin / extension architectures:**

- Plugins that implement a declared interface — each plugin is a scope group candidate if it is self-contained
- Middleware chains — individual middleware components are scope group candidates only if they contain significant logic; trivial pass-through middleware belongs with its host pipeline
- Service / repository pairs — a service interface + repository interface + their implementations form a layered feature scope group

**Deviations from framework conventions:**

- Logic in views — business logic in `UIViewController`, React component bodies, or Blazor `.razor` files that should be in a ViewModel or service
- Fat models — domain models with persistence, validation, and business logic mixed in one class
- God services — a single service class handling many unrelated concerns
- Missing abstraction layers — direct API calls from UI components without a service or repository intermediary

## Boundary Detection

1. **Framework-conventional units are the default scope group.** When the codebase follows framework conventions, those conventions define the scope groups. Do not decompose below the conventional unit without strong evidence from other lenses.
2. **Cross-feature sharing elevates to its own scope group.** A ViewModel or service referenced by three or more feature modules is no longer feature-local — it belongs in a shared scope group.
3. **Deviations are flagged, not respected.** If logic is placed in the wrong layer (business logic in a view), note the deviation — do not create a scope group that legitimizes the misplacement.
4. **Lazy-loaded modules are independent scope groups.** Any module configured for lazy loading in Angular, Next.js dynamic imports, or Webpack code splitting is designed to be independently loadable — treat it as an independent scope group.
5. **Plugin/extension registries are composition roots.** The registry that loads and wires plugins is a separate scope group from the plugins themselves.

## Findings Format

```
FRAMEWORK CONVENTIONS FINDINGS
================================

Detected Framework(s): <list — e.g., "SwiftUI + The Composable Architecture", "React + Redux Toolkit">

Conventional Units Found:
  - <Pattern> (<Framework>) — count: <n>, files per unit: <avg>
    Example: <representative unit name and files>

Convention Violations:
  - <description — e.g., "Business logic in 6 UIViewController subclasses — should be in ViewModels">
  - <description — e.g., "CartViewController directly calls NetworkClient — missing service layer">

Lazy-Loaded / Code-Split Boundaries:
  - <ModuleName> — trigger: <e.g., "route /checkout", "user navigates to settings">

Shared Conventional Units (used by 3+ features):
  - <Name> — shared by: <list>

Recommended Scope Group Candidates:
  - <Name> — <framework pattern>, <one-line rationale>
```

## Change History
