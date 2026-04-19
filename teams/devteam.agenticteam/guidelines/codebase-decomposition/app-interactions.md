---

id: 1d4b2aa7-c30e-4d41-8bd8-892ff7ce7499
title: "App Interactions"
domain: agentic-cookbook://guidelines/planning/code-quality/app-interactions
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Characterize how components communicate within the application — delegation, pub/sub, shared state, and other in-process coordination patterns."
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

# App Interactions

The communication patterns between components reveal how tightly or loosely they are coupled. A component that communicates only through a narrow delegate protocol is loosely coupled and independently testable. A component that reads and writes shared mutable state is tightly coupled to everything that touches that state. This lens maps the in-process communication patterns to understand where the real dependencies lie — which may differ substantially from what the import graph shows.

## Signals and Indicators

**Delegation patterns:**

- Swift: `weak var delegate: SomeDelegate?` properties; protocol declarations named `*Delegate`, `*DataSource`; `delegate?.someMethod()` call sites
- Objective-C: `@protocol` declarations; `id<Protocol>` typed delegate properties
- Kotlin: interface-based delegation; `by` keyword delegation
- C#: `event` declarations; delegate types; `EventHandler<T>` patterns
- TypeScript: callback props in React (`onPress`, `onChange`, `onSubmit`); callback-typed interface fields

**Observer and notification patterns:**

- iOS: `NotificationCenter.default.addObserver()` / `post(name:)` — note the notification name, sender, and observer registration site. Each notification is an implicit coupling between poster and observer.
- Android: `LocalBroadcastManager`, `EventBus`, `LiveData.observe()`, `Flow.collect()`, `BroadcastReceiver`
- C#: `IObservable<T>` / `IObserver<T>`; Reactive Extensions (`Rx.NET`); `WeakReference` event subscriptions
- Web: `addEventListener` / `dispatchEvent`; custom `EventEmitter`; `window.postMessage`; `BroadcastChannel`
- Reactive frameworks: `Combine` (Swift), `RxSwift`, `RxKotlin`, `RxJS` — publisher/subscriber chains; note where publishers are created vs where subscribers attach

**Shared state and singletons:**

- Global or class-level `static var shared` / `static let shared` — singleton access points
- `UserDefaults` / `SharedPreferences` / `localStorage` reads and writes — shared mutable state accessed by key string
- Global state containers: Redux store, MobX observables, Zustand store, Vuex store, `@EnvironmentObject` (SwiftUI), `Context` (React)
- Thread-local or actor-isolated state — note the isolation boundary

**Dependency injection:**

- Constructor injection — dependencies passed as initializer arguments; clean coupling, easy to test
- Property injection — `var service: SomeService?` set after construction; looser coupling but less explicit
- DI containers: Swinject, Hilt, Dagger, Spring, Koin, inversify — note registration vs resolution sites
- `@Environment` / `@EnvironmentObject` (SwiftUI), `@Inject` / `@Provides` (Hilt/Dagger), `@Injectable` (Angular)

**Navigation and routing:**

- Coordinator pattern — a coordinator object owns navigation decisions and routes between screens
- Router pattern — centralized routing table; routes referenced by name or enum case
- Direct `present()`, `push()`, `navigate()`, `startActivity()` calls from within a view — tight coupling between view and navigation
- Deep link handlers — URL-to-screen mapping centralized in a router or scattered across app delegates
- Navigation state in global store (React Navigation, SwiftUI `NavigationPath`) — navigation is shared state

**Callback chains:**

- Completion handler chains — `func doThing(completion: @escaping (Result) -> Void)` — note depth; chains of 3+ levels suggest refactoring to async/await
- Promise chains — `.then().then().catch()` — note where error handling breaks the chain
- `async/await` call chains — cleaner but still represent control flow coupling

**Event buses:**

- Named event systems: custom `EventBus`, `MessageBus`, `PubSub` implementations
- Cross-component event dispatching where event consumer is not statically known at definition time

## Boundary Detection

1. **Delegation defines interface boundaries.** A component with a clean delegate protocol is designed to be replaceable — the delegate protocol IS the interface. The component and its protocol belong in the same scope group; its concrete delegate implementations may belong elsewhere.
2. **Notification center usage is an implicit coupling signal.** For every `NotificationCenter.post`, identify all files that observe that notification — they are implicitly coupled even if they have no import relationship. High use of notifications across many files indicates missing formal interfaces.
3. **Singletons couple everything to everything.** Any file that accesses a singleton is implicitly coupled to every other file that accesses the same singleton. Singletons accessed across many candidate groups indicate a cross-cutting dependency — flag for `cross-cutting-detection`.
4. **DI containers define the composition boundary.** The DI container registration site is the architectural seam — it is where modules are wired together. Code on either side of the registration site belongs in separate scope groups.
5. **Coordinators are natural scope group boundaries.** A coordinator object that manages navigation for a feature flow — and owns the child view controllers in that flow — is a natural scope group boundary. The coordinator and its owned screens form one group.
6. **Global state (Redux, MobX, Context) makes boundaries fuzzy.** If all components read from a single global store, module boundaries are implicitly bypassed. Document which store slices each candidate group reads/writes — slices may suggest sub-boundaries.

## Findings Format

```
APP INTERACTIONS FINDINGS
==========================

Delegation Patterns:
  - <ProtocolName> — defined in: <file>, implemented by: <file list>

Notification/Event Patterns:
  - <NotificationName> — posted in: <file list>, observed in: <file list>
    Coupling scope: <"within one directory" | "crosses multiple directories">

Shared State:
  - <StateDescription> (<mechanism>) — read by: <n> files, written by: <n> files
    Scope: <"local to one group" | "cross-group — flag as cross-cutting">

Dependency Injection:
  - DI mechanism: <e.g., "Swinject container in AppDelegate", "Hilt modules">
  - Registration sites: <file list>
  - Injection points: <count and description>

Navigation/Routing:
  - Pattern: <e.g., "Coordinator", "centralized Router", "direct push from view">
  - Coordinator/Router files: <list>
  - Deep link handler: <file>

Coupling Anomalies:
  - <description — e.g., "HomeViewController directly calls PaymentService.shared — bypasses dependency injection">

Recommended Scope Group Candidates:
  - <Name> — <primary interaction pattern>, <one-line rationale>
```

## Change History
