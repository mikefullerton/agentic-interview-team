---
name: native-controls
description: Use platform built-in frameworks before custom implementations; WorkManager over raw thread scheduling; Room over raw SQ...
artifact: principles/native-controls.md
version: 1.0.0
---

## Worker Focus
Use platform built-in frameworks before custom implementations; WorkManager over raw thread scheduling; Room over raw SQLite; OkHttp/Retrofit over custom HTTP; note explicitly which native controls are used and why

## Verify
No custom reimplementations of standard Material components; background work uses WorkManager; data persistence uses Room; HTTP uses OkHttp or Retrofit
