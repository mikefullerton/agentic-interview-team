---

id: 6302654b-8200-4e03-862d-4734d4960d19
title: "No blocking the main thread"
domain: agentic-cookbook://guidelines/implementing/concurrency/concurrency
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "All lengthy work must run on background threads/tasks using platform async primitives:"
platforms: 
  - csharp
  - kotlin
  - python
  - swift
  - typescript
  - web
  - windows
tags: 
  - concurrency
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - concurrency
  - performance-optimization
---

# No blocking the main thread

All lengthy work must run on background threads/tasks using platform async primitives:

- **Apple**: Swift Concurrency (`async`/`await`, `Task`, actors)
- **Android**: Kotlin Coroutines (`viewModelScope`, `Dispatchers.IO`)
- **Web**: `Promise`/`async`, Web Workers
- **Python**: `asyncio`, threading for I/O
- **Windows/.NET**: `async`/`await`, `Task.Run` for CPU-bound work, `DispatcherQueue` for UI updates

The main/UI thread MUST NOT be blocked.

---

# Concurrency

All lengthy work MUST run on background threads/tasks using platform async primitives. The main/UI thread MUST NOT be blocked. Progress SHOULD be shown (determinate or indeterminate) when the UI is waiting on an async task.

## Swift

Use Swift Concurrency (`async`/`await`, `Task`, actors) for all async work. Never block the main thread. Use `@MainActor` for UI updates.

## Kotlin

Use Kotlin Coroutines for all async work. Run I/O on `Dispatchers.IO`. Use `viewModelScope` for ViewModel-scoped coroutines. Never block the main thread.

```kotlin
viewModelScope.launch(Dispatchers.IO) {
    val result = repository.fetch()
    withContext(Dispatchers.Main) { updateUi(result) }
}
```

## TypeScript

Use `Promise`/`async`/`await` for async operations. Use Web Workers for CPU-intensive tasks. Never block the main thread.

## C#

Use `async`/`await` for all async work. Never block the main thread.

- `ConfigureAwait(false)` in library code to avoid capturing the synchronization context
- `.Result` or `.Wait()` MUST NOT be used — causes deadlocks
- `async void` MUST NOT be used except for event handlers
- All async APIs MUST accept `CancellationToken`
- Use `ValueTask<T>` only when the method frequently completes synchronously
- Use `Task.Run` for CPU-bound work, never on the UI thread

```csharp
// Library code — ConfigureAwait(false)
public async Task<Data> FetchAsync(CancellationToken ct = default)
{
    var response = await _client.GetAsync(url, ct).ConfigureAwait(false);
    return await ParseAsync(response, ct).ConfigureAwait(false);
}

// Application code — no ConfigureAwait needed
public async Task OnLoadAsync()
{
    var data = await _service.FetchAsync();
    UpdateUI(data);
}
```

## Windows

Same async/await conventions as C# above. For WinUI 3 specifically:

- Use `DispatcherQueue.TryEnqueue` to marshal work back to the UI thread from background tasks
- Never access UI elements from non-UI threads

```csharp
DispatcherQueue.TryEnqueue(() =>
{
    StatusText.Text = "Updated from background";
});
```

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
