---
name: widgets-and-glanceable-surfaces
description: Use Jetpack Glance with Compose-style APIs for home screen widgets; define widget metadata in `appwidget-provider` XML; ...
artifact: guidelines/platform/widgets-and-glanceable-surfaces.md
version: 1.0.0
---

## Worker Focus
Use Jetpack Glance with Compose-style APIs for home screen widgets; define widget metadata in `appwidget-provider` XML; support resizable widgets and respond to `onUpdate` broadcasts; use `WorkManager` for background data refresh; follow Material You theming for visual consistency; tapping widget must deep link to relevant content

## Verify
`appwidget-provider` XML present; `onUpdate` broadcast handled; widget tap navigates to correct content; Material You theming applied; `WorkManager` used for data refresh
