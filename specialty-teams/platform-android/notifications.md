---
name: notifications
description: Use `NotificationCompat.Builder` for backward-compatible notifications; declare `NotificationChannel` so users control c...
artifact: guidelines/platform/notifications.md
version: 1.0.0
---

## Worker Focus
Use `NotificationCompat.Builder` for backward-compatible notifications; declare `NotificationChannel` so users control categories individually; permission requested at moment of relevance (Android 13+ requires `POST_NOTIFICATIONS`); support Direct Reply, bubbles, and conversation style for messaging; every notification deep links to relevant content

## Verify
`NotificationChannel` declared for each notification category; `POST_NOTIFICATIONS` permission requested at relevant moment; notification tap deep links to content; no notifications sent without runtime permission on Android 13+
