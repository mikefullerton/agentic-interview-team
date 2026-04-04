---
name: concurrency
description: All lengthy work on background threads using platform async primitives (Swift Concurrency, Kotlin Coroutines, Promise/as...
artifact: guidelines/concurrency/concurrency.md
version: 1.0.0
---

## Worker Focus
All lengthy work on background threads using platform async primitives (Swift Concurrency, Kotlin Coroutines, Promise/async, asyncio, async/await on .NET); never block the main/UI thread; show progress when UI is waiting on an async task; C# specifics: ConfigureAwait(false) in library code, no .Result/.Wait(), CancellationToken in all async APIs

## Verify
No synchronous I/O or network calls on main/UI thread; async/await used throughout (no .Result/.Wait() in C#); CancellationToken accepted by async APIs; progress shown in UI while awaiting background work
