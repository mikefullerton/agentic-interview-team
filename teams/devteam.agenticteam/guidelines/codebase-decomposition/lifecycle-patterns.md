---

id: 918c4cec-0bc5-45bf-86d0-5a795053400f
title: "Lifecycle Patterns"
domain: agentic-cookbook://guidelines/planning/code-quality/lifecycle-patterns
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Identify scope group boundaries by finding groups of objects that are created, owned, and destroyed together as a unit."
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

# Lifecycle Patterns

Objects that are born together, live together, and die together form a natural unit. Lifecycle patterns reveal ownership hierarchies — which object is responsible for creating and destroying which other objects — and resource management strategies — how connections, sessions, and acquired capabilities are released. This lens identifies clusters of objects that share a common lifecycle, because those clusters cannot be independently deployed or tested without bringing their lifecycle peers along.

## Signals and Indicators

**Construction and initialization:**

- Custom `init` / constructor with dependency parameters — the set of parameters reveals what the object owns vs borrows
- Factory methods — `SomeClass.make()`, `SomeClass.create(with:)`, static constructors — note what the factory assembles
- Builder patterns — `SomeBuilder().withX().withY().build()` — the builder collects all initialization dependencies; the built object's lifecycle starts at `build()`
- Two-phase initialization — `init()` followed by explicit `setup()` / `configure()` / `start()` — note what state exists between phases
- `@objc func awakeFromNib()` / `viewDidLoad()` — lifecycle initialization in the view layer tied to the host view controller's own lifecycle

**Teardown and cleanup:**

- `deinit` (Swift), `finalize()` (Java), destructor `~ClassName()` (C++), `Dispose()` / `IDisposable` (C#), `close()` / `Closeable` (Java/Kotlin) — note what resources are released
- `onDestroy()`, `onStop()`, `viewWillDisappear()`, `componentWillUnmount()` — framework-managed teardown hooks; note what cleanup is performed
- Explicit `cancel()`, `invalidate()`, `stop()`, `shutdown()` calls — active teardown beyond simple deallocation
- `defer` blocks (Swift/Go) — resource cleanup guaranteed at scope exit
- `using` (C#), `try-with-resources` (Java), `with` statement (Python) — automatic resource management scope

**Retain and memory management:**

- `weak` / `unowned` references in Swift — indicates shared ownership or prevents cycles; the `weak` end does not participate in the lifecycle of the `strong` end
- `WeakReference<T>` in Kotlin/Java/C# — same semantics
- Reference counting in C++ (`shared_ptr` / `weak_ptr`) — ownership semantics explicit in type
- `@autoreleasepool` blocks — scope-limited memory management
- Capture lists in closures — `[weak self]` vs `[unowned self]` vs strong capture — strong capture extends lifetime

**Connection and session management:**

- Database connection pools — `ConnectionPool`, `DBQueue` (GRDB), `Core Data` persistent container — connections acquired and returned
- Network session objects — `URLSession`, `OkHttpClient`, `HttpClient` — note whether sessions are per-request or long-lived
- WebSocket connections — establish, maintain, reconnect, close — a distinct lifecycle unit
- Bluetooth peripheral connections — `CBCentralManager` connect/disconnect cycle
- Authentication sessions — login → token refresh → logout; the token's validity window IS the session lifecycle

**State machines:**

- Explicit state enums with associated values — `enum State { case idle, loading, loaded(Data), error(Error) }` — the state machine is a lifecycle in data
- State transition methods — `func transitionTo(_ state: State)` — note valid transitions
- Reactive state sequences — `@Published var state: State` (Combine), `StateFlow` (Kotlin), `BehaviorSubject` (RxSwift/RxKotlin) — the stream IS the state machine

**Resource ownership and disposal:**

- Subscription storage — `var cancellables = Set<AnyCancellable>()` (Combine), `disposeBag: DisposeBag` (RxSwift), `compositeDisposable` (RxJava) — the object that holds the storage bag owns the subscription lifecycle
- Timer lifecycle — `Timer.scheduledTimer()` must be invalidated; note where invalidation happens relative to the owning object's teardown
- `NotificationCenter` observer registration — note whether removal is explicit (`removeObserver`) or managed by token disposal

**Pooling and reuse:**

- Object pools — `ReusablePool`, cell reuse in `UITableView`/`RecyclerView` — objects are not destroyed but returned; their lifecycle is the pool's lifecycle, not the consumer's
- View recycling — `prepareForReuse()` — an intermediate lifecycle event between allocation and consumer use

## Boundary Detection

1. **Shared init/deinit = same scope group.** If object A creates object B in its `init` and destroys it in its `deinit`, A owns B and they belong together.
2. **Subscription ownership defines lifecycle coupling.** If object A stores a `Cancellable` / `DisposeBag` subscription to object B's stream, A's lifecycle bounds the subscription — A and B are lifecycle-coupled.
3. **State machines are atomic.** An explicit state machine — all states, transitions, and the object that executes them — is a single unit. Do not split state machines across scope groups.
4. **Session objects define natural scope group boundaries.** A session — authentication session, network session, user session — and all objects that exist only for the duration of that session form one scope group.
5. **Weak references mark scope group edges.** A `weak` reference from A to B means B does not own A. If A's lifecycle is independent of B's, they may belong in separate scope groups communicating through a narrow interface.
6. **Disposal chain = lifecycle chain.** Follow `Dispose()` / `cancel()` / `close()` calls — each object that disposes another is part of the same lifecycle chain.

## Findings Format

```
LIFECYCLE PATTERNS FINDINGS
============================

Object Creation Hierarchies:
  - <OwnerObject> creates: <list of owned objects>
    Created in: <init | factory | two-phase setup>
    Destroyed in: <deinit | explicit teardown | disposal>

Session/Connection Lifecycles:
  - <SessionType> — start: <trigger>, end: <trigger>, managed in: <file>
    Duration: <e.g., "per request" | "per user session" | "app lifetime">

State Machines:
  - <StateMachine> — states: <list>, file(s): <list>
    Transitions driven by: <e.g., "user action" | "network response" | "timer">

Subscription Ownership:
  - <File> owns subscriptions to: <list of publishers/observables>
    Storage mechanism: <e.g., "AnyCancellable Set", "DisposeBag">

Resource Management Patterns:
  - <Pattern> — used in: <file list>, resource managed: <description>

Lifecycle Anomalies:
  - <description — e.g., "Timer created in viewDidLoad never invalidated — potential leak">
  - <description — e.g., "Two-phase init with no clear invariants between phases">

Recommended Scope Group Candidates:
  - <Name> — <lifecycle anchor object>, <one-line rationale>
```

## Change History
