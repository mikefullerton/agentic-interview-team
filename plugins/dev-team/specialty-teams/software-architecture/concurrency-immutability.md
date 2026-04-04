---
name: concurrency-immutability
description: Default to immutable values; introduce mutability only where necessary; prefer value types over reference types; contain...
artifact: guidelines/concurrency/immutability.md
version: 1.0.0
---

## Worker Focus
Default to immutable values; introduce mutability only where necessary; prefer value types over reference types; contain mutation behind clear boundaries; Kotlin: val/data class/StateFlow; TypeScript: const/useState; C#: readonly/record/ImmutableList

## Verify
Shared data structures are immutable by default; mutable state contained behind StateFlow/ObservableObject/thread-safe wrappers; C# DTOs use record types; no mutable shared fields accessed from multiple concurrent contexts without synchronization
