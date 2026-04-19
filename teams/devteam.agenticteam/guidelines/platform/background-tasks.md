---

id: 433b4c9d-fe44-4fec-af0d-83bba9c51c6f
title: "Background tasks"
domain: agentic-cookbook://guidelines/implementing/platform-integration/background-tasks
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-02
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Apps that sync data, process uploads, or maintain state SHOULD use platform background execution APIs rather than relying on foreground presence."
platforms: 
  - ios
  - macos
  - android
  - windows
  - web
tags: 
  - background-tasks
  - platform
  - sync
depends-on: []
related:
  - agentic-cookbook://guidelines/platform/notifications
  - agentic-cookbook://guidelines/networking/offline-and-connectivity
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - platform-integration
  - concurrency
---

# Background tasks

Apps that sync data, process uploads, or maintain state SHOULD use platform background execution APIs rather than relying on foreground presence. Background tasks extend the app's usefulness while the user is doing other things.

- Use the platform's sanctioned background APIs — unsanctioned workarounds get killed and drain battery
- Design tasks to be resumable — background execution can be interrupted at any time
- Minimize resource usage — the OS budgets CPU and network time strictly
- Report progress and completion through notifications when appropriate

## Apple (iOS / macOS)

Use `BGAppRefreshTask` and `BGProcessingTask` via the BackgroundTasks framework for deferred work. Use `URLSession` background transfers for uploads and downloads that survive app suspension. On macOS, longer-running background work is less restricted but should still use `ProcessInfo.performActivity` to prevent App Nap. Use `NSBackgroundActivityScheduler` for periodic maintenance tasks on macOS.

## Android

Use `WorkManager` for all deferrable background work — it handles constraints, retries, and chaining. Use `ForegroundService` with a persistent notification for user-visible ongoing work (music playback, navigation, uploads). Respect Doze mode and App Standby buckets. Avoid `AlarmManager` for work that `WorkManager` can handle.

## Windows

Use `BackgroundTask` with the Windows App SDK for background execution. Register triggers (time, network state change, push notification) in the app manifest. For long-running tasks, use `ExtendedExecutionSession`. Background tasks in MSIX-packaged apps run in a separate process with limited resource access.

## Web

Use Service Workers for background sync (`BackgroundSyncManager`) and push notification handling. Use the Periodic Background Sync API for recurring data refresh (requires PWA install and user engagement). Use Web Workers for CPU-intensive tasks that shouldn't block the UI thread. Fall back to `requestIdleCallback` for low-priority deferred work.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-02 | Mike Fullerton | Initial creation |
