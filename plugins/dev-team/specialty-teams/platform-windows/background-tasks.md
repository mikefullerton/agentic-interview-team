---
name: background-tasks
description: Use `BackgroundTask` with Windows App SDK for background execution; register triggers (time, network state change, push ...
artifact: guidelines/platform/background-tasks.md
version: 1.0.0
---

## Worker Focus
Use `BackgroundTask` with Windows App SDK for background execution; register triggers (time, network state change, push notification) in app manifest; for long-running tasks use `ExtendedExecutionSession`; background tasks in MSIX run in separate process with limited resource access; design tasks to be resumable

## Verify
Background task triggers declared in `Package.appxmanifest`; `ExtendedExecutionSession` used for long-running operations; tasks handle interruption and restart gracefully; no reliance on foreground presence for critical sync
