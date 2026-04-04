---
name: background-tasks
description: Use `WorkManager` for all deferrable background work — handles constraints, retries, and chaining; use `ForegroundServic...
artifact: guidelines/platform/background-tasks.md
version: 1.0.0
---

## Worker Focus
Use `WorkManager` for all deferrable background work — handles constraints, retries, and chaining; use `ForegroundService` with persistent notification for user-visible ongoing work; respect Doze mode and App Standby buckets; avoid `AlarmManager` for work WorkManager can handle; design tasks to be resumable

## Verify
Deferrable work uses `WorkManager`; no direct `AlarmManager` usage for periodic tasks; foreground services have persistent notifications; tasks handle interruption and retry gracefully
