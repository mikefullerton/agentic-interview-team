---
name: native-controls
description: Use platform built-in frameworks before custom implementations; Swift Concurrency over raw threads; SwiftData/Core Data ...
artifact: principles/native-controls.md
version: 1.0.0
---

## Worker Focus
Use platform built-in frameworks before custom implementations; Swift Concurrency over raw threads; SwiftData/Core Data over raw SQLite; URLSession over custom HTTP; note explicitly which native controls are used and why

## Verify
No custom reimplementations of standard iOS controls; concurrency uses async/await or Actors; data persistence uses SwiftData or Core Data; HTTP uses URLSession
