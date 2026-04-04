---
name: background-tasks
description: Use `BGAppRefreshTask` and `BGProcessingTask` via BackgroundTasks framework for deferred work; use `URLSession` backgrou...
artifact: guidelines/platform/background-tasks.md
version: 1.0.0
---

## Worker Focus
Use `BGAppRefreshTask` and `BGProcessingTask` via BackgroundTasks framework for deferred work; use `URLSession` background transfers for uploads/downloads that survive suspension; on macOS use `ProcessInfo.performActivity` and `NSBackgroundActivityScheduler`; design tasks to be resumable

## Verify
No foreground-only sync logic; `BGAppRefreshTask`/`BGProcessingTask` registered and handled; `URLSession` background configuration used for transfers; tasks handle interruption gracefully
