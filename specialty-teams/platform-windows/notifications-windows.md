---
name: notifications-windows
description: Use `AppNotificationManager` + `AppNotificationBuilder` fluent API for local notifications; support text, images, button...
artifact: guidelines/platform/notifications.md
version: 1.0.0
---

## Worker Focus
Use `AppNotificationManager` + `AppNotificationBuilder` fluent API for local notifications; support text, images, buttons with activation arguments, progress bars, and scheduled delivery; handle notification activation alongside protocol activation; MSIX-packaged apps get notification identity automatically; request permission at moment of relevance

## Verify
`AppNotificationManager` used (not legacy toast APIs); activation arguments handled in `OnLaunched`; notification tap navigates to relevant content; scheduled notifications use correct delivery time; no notifications sent before permission granted
