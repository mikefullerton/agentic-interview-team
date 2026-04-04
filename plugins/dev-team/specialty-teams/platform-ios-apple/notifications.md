---
name: notifications
description: Use `UNUserNotificationCenter` for local and push notifications; permission requested at moment of relevance, not at lau...
artifact: guidelines/platform/notifications.md
version: 1.0.0
---

## Worker Focus
Use `UNUserNotificationCenter` for local and push notifications; permission requested at moment of relevance, not at launch; support `UNNotificationCategory` and `UNNotificationAction` for actionable notifications; every notification deep links to relevant content; respect iOS interruption levels (Time Sensitive, Notification Summary)

## Verify
Permission request deferred to relevant moment; `UNNotificationCategory` registered with actions; notification tap deep links to content; no notifications sent without user permission
