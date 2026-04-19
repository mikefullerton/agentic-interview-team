---

id: 94e8caba-da27-4bb8-8f8e-38730b8b34e0
title: "Notifications"
domain: agentic-cookbook://guidelines/implementing/platform-integration/notifications
type: guideline
version: 2.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Apps SHOULD use the platform notification system for timely, actionable alerts that respect user preferences."
platforms: 
  - ios
  - macos
  - android
  - windows
  - web
tags: 
  - notifications
  - platform
depends-on:
  - agentic-cookbook://principles/support-automation
related:
  - agentic-cookbook://guidelines/platform/deep-linking
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - platform-integration
  - ui-implementation
---

# Notifications

Apps SHOULD use the platform notification system for timely, actionable alerts that respect user preferences. Notifications are a shared system resource — misuse erodes trust and leads to users disabling them entirely.

- Request permission at the moment of relevance, not at launch
- Every notification MUST be actionable — tapping it deep links to the relevant content
- Support notification grouping and categories to reduce clutter
- Respect Do Not Disturb, Focus modes, and quiet hours

## Apple (iOS / macOS)

Use `UNUserNotificationCenter` for local and push notifications. Support actionable notifications with `UNNotificationCategory` and `UNNotificationAction`. On iOS, support Notification Summary and Time Sensitive interruption levels.

## Android

Use `NotificationCompat.Builder` for backward-compatible notifications. Declare notification channels (`NotificationChannel`) so users can control categories individually. Support Direct Reply, bubbles, and conversation style for messaging apps.

## Windows

Use `AppNotificationManager` + `AppNotificationBuilder` fluent API for local notifications. Support text, images, buttons with activation arguments, progress bars, and scheduled delivery. Handle notification activation alongside protocol activation. MSIX-packaged apps get notification identity automatically.

## Web

Use the Notifications API with service workers for push notifications. Request permission contextually. Support notification actions and badges via the Badging API. Fall back gracefully when notifications are denied or unavailable.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 2.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 2.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation (Windows only) |
| 2.0.0 | 2026-04-02 | Mike Fullerton | Promoted to cross-platform guideline with iOS, Android, macOS, web coverage |
