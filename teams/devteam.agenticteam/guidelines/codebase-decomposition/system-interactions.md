---

id: e8c8e3b9-64a0-4fb0-a27b-f3b733dc10c7
title: "System Interactions"
domain: agentic-cookbook://guidelines/planning/code-quality/system-interactions
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Characterize how the code communicates with the operating system — IPC, lifecycle callbacks, background execution, and OS-level integration points."
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

# System Interactions

The operating system is not passive. It invokes callbacks, manages process lifecycle, delivers notifications, routes URLs, and terminates background work. Code that participates in OS-managed lifecycles has a fundamentally different structure than code that runs only when explicitly called. This lens identifies where the codebase touches the OS boundary — not to use system frameworks (see `system-dependencies`), but to participate in OS-managed communication, lifecycle, and integration protocols.

## Signals and Indicators

**Application lifecycle callbacks:**

- iOS/macOS: `UIApplicationDelegate` methods — `application(_:didFinishLaunchingWithOptions:)`, `applicationDidBecomeActive`, `applicationWillResignActive`, `applicationDidEnterBackground`, `applicationWillTerminate`; `SceneDelegate` equivalents for multi-window
- Android: `Activity.onCreate/onStart/onResume/onPause/onStop/onDestroy`, `Service.onCreate/onStartCommand`, `Application.onCreate`, `ContentProvider.onCreate`
- Web: `DOMContentLoaded`, `load`, `beforeunload`, `unload`, `visibilitychange`, `pageshow`/`pagehide`; Service Worker lifecycle (`install`, `activate`, `fetch`)
- Windows: `OnLaunched`, `OnSuspending`, `OnResuming` (UWP); `Application_Startup`, `Application_Exit` (WPF); `Main()` entry point with message loop

**Background execution:**

- iOS: `BGTaskScheduler.submit()`, `beginBackgroundTask(withName:)`, `URLSession` background download/upload tasks, `WKExtensionDelegate` background fetch
- Android: `WorkManager`, `JobScheduler`, `AlarmManager`, `Service` with `START_STICKY`, `BroadcastReceiver` for system events
- Web: Service Worker `sync` event, `BackgroundFetch API`, `Periodic Background Sync`
- Windows: Background tasks via `IBackgroundTask`, `AppService` connections

**Interprocess communication (IPC):**

- iOS: App Extensions communicate via shared containers or `NSXPCConnection`; `openURL` to other apps; `CFMessagePort`; Pasteboard for cross-process data
- Android: `Intent` system (explicit and implicit); `ContentProvider` for structured data sharing; `AIDL` interfaces; `Messenger`
- Windows: Named pipes (`NamedPipeServerStream`/`NamedPipeClientStream`); COM/DCOM; WCF (Windows Communication Foundation); `MemoryMappedFile` for shared memory
- Web: `window.postMessage` cross-origin; `SharedWorker`; `BroadcastChannel`; `MessageChannel`; Service Worker message passing

**Push notifications and remote events:**

- iOS: `UNUserNotificationCenter` delegate methods; `application(_:didReceiveRemoteNotification:)` in AppDelegate; `UNNotificationServiceExtension` for content modification
- Android: `FirebaseMessagingService.onMessageReceived()`; notification channel creation; `PendingIntent` for notification actions
- Web: `ServiceWorkerRegistration.showNotification()`; `push` event in Service Worker; `notificationclick` handler
- Windows: `ToastNotification`; `BadgeUpdateManager`; `TileUpdateManager`

**URL schemes and deep links:**

- iOS: `application(_:open:options:)` for custom URL schemes; `application(_:continue:restorationHandler:)` for Universal Links; `UIApplicationShortcutItem` for home screen quick actions
- Android: `Intent` filters with `ACTION_VIEW` and URI patterns in `AndroidManifest.xml`; `onNewIntent()` handling
- Web: Protocol handlers (`registerProtocolHandler`); Progressive Web App URL handling in `manifest.json`
- Windows: Protocol activation in `Package.appxmanifest`; `OnActivated` handler in App class

**File system and OS integration:**

- Document provider extensions (iOS `UIDocumentPickerViewController`, Android Storage Access Framework, Windows `FileOpenPicker`)
- File watching / directory monitoring (`FSEvents`, `inotify`, `FileSystemWatcher`, `ReadDirectoryChangesW`)
- Socket communication (Unix domain sockets, TCP sockets for localhost IPC)

**Keyboard, accessibility, and input system integration:**

- Custom keyboard extensions (iOS `UIInputViewController`)
- Accessibility tree callbacks (`UIAccessibility`, `AccessibilityService` on Android)
- Input Method Editor (IME) integration
- Global keyboard shortcut registration

## Boundary Detection

1. **Lifecycle callback implementations are natural scope group anchors.** Files that implement `UIApplicationDelegate`, `AndroidApplication`, or equivalent are the entry points of the application — they are architectural seams where scope groups plug in.
2. **Each OS integration point is a potential boundary.** A file that handles push notification payloads is in the notification scope group. A file that handles URL scheme routing is in the routing/deep-link scope group. Treat each OS integration point as a distinct concern.
3. **Background execution code belongs in its own scope group.** Background tasks have distinct lifecycle, resource, and testing constraints. Code that runs in background contexts should not be mixed with foreground UI code.
4. **IPC code is infrastructure.** An app extension that communicates with its host app via shared container is infrastructure-layer code — it should be grouped with other infrastructure, not with the feature it serves.
5. **Lifecycle callbacks that dispatch to many subsystems are composition roots.** An `AppDelegate` that calls 15 different services is a composition root, not a feature — it belongs in an `App` or `Bootstrap` scope group that wires everything together.

## Findings Format

```
SYSTEM INTERACTIONS FINDINGS
=============================

Application Lifecycle:
  - <Platform> lifecycle callbacks in: <file list>
    Callbacks implemented: <list — e.g., "didFinishLaunching, didEnterBackground">
    Services initialized in launch: <list>

Background Execution:
  - <Mechanism> — purpose: <description>, implemented in: <file list>

IPC Mechanisms:
  - <Mechanism> — direction: <"in" | "out" | "bidirectional">, files: <list>

Push Notifications:
  - Handler file(s): <list>
  - Payload types handled: <description>

URL Schemes / Deep Links:
  - Schemes: <list>, handler: <file>
  - Universal Link domains: <list>

OS Integration Points:
  - <Integration> — files: <list>, purpose: <description>

Lifecycle Anomalies:
  - <description — e.g., "AppDelegate initializes 12 unrelated services — should be decomposed into startup tasks">

Recommended Scope Group Candidates:
  - <Name> — <primary OS integration>, <one-line rationale>
```

## Change History
