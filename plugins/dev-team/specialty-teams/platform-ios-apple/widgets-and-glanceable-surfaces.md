---
name: widgets-and-glanceable-surfaces
description: Use WidgetKit with SwiftUI views (one of the mandated SwiftUI surfaces); support small, medium, and large families; on i...
artifact: guidelines/platform/widgets-and-glanceable-surfaces.md
version: 1.0.0
---

## Worker Focus
Use WidgetKit with SwiftUI views (one of the mandated SwiftUI surfaces); support small, medium, and large families; on iOS 17+ support interactive widgets with `AppIntent`-backed buttons; on iOS 16+ support Lock Screen widgets; use `TimelineProvider` for scheduled updates; tapping widget must deep link to relevant content; use `ActivityKit` for Live Activities with Dynamic Island

## Verify
Widget supports at least small and medium families; `TimelineProvider` implemented; widget tap navigates to correct content; interactive widget actions backed by `AppIntent`; no SwiftUI deprecated navigation APIs in widget
