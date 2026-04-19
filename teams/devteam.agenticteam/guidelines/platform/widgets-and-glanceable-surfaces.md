---

id: e3aa9294-61cf-4a3a-9fbf-0528a1404094
title: "Widgets and glanceable surfaces"
domain: agentic-cookbook://guidelines/implementing/platform-integration/widgets-and-glanceable-surfaces
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-02
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Apps with time-sensitive or frequently checked data SHOULD provide widgets and glanceable surfaces on platforms that support them."
platforms: 
  - ios
  - macos
  - android
  - web
tags: 
  - widgets
  - platform
  - glanceable
depends-on:
  - agentic-cookbook://principles/support-automation
related:
  - agentic-cookbook://guidelines/platform/notifications
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - platform-integration
  - ui-implementation
---

# Widgets and glanceable surfaces

Apps with time-sensitive or frequently checked data SHOULD provide widgets and glanceable surfaces on platforms that support them. Widgets let users consume information and take action without launching the full app.

- Show only the most important information — widgets are not miniature apps
- Support multiple widget sizes when the platform offers them
- Tapping a widget MUST deep link to the relevant content in the app
- Update widget content on a reasonable cadence — balance freshness against battery and data usage

## Apple (iOS / macOS)

Use WidgetKit with SwiftUI views. Support small, medium, and large widget families. On iOS 17+, support interactive widgets with `AppIntent`-backed buttons and toggles. On iOS 16+, support Lock Screen widgets. Use `TimelineProvider` for scheduled updates and `WidgetCenter.shared.reloadTimelines` for event-driven refresh.

For real-time status, use Live Activities with `ActivityKit` and the Dynamic Island on supported devices.

## Android

Use Jetpack Glance with Compose-style APIs for home screen widgets. Define widget metadata in `appwidget-provider` XML. Support resizable widgets and respond to `onUpdate` broadcasts. Use `WorkManager` for background data refresh. Follow Material You theming for visual consistency with the system.

## Web (PWA)

Use the Badging API for app icon notification counts. Support periodic background sync via service workers for data freshness. Explore experimental Widget API proposals where available. On desktop PWAs, consider system tray or menu bar presence where the platform allows.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-02 | Mike Fullerton | Initial creation |
