---
name: design-time-data
description: Use `d:DataContext` and `d:DesignInstance` for XAML designer preview data; use XAML Hot Reload for live iteration during...
artifact: guidelines/platform/windows/design-time-data.md
version: 1.0.0
---

## Worker Focus
Use `d:DataContext` and `d:DesignInstance` for XAML designer preview data; use XAML Hot Reload for live iteration during development; keep design-time data classes lightweight and separate from production code

## Verify
XAML views have `d:DataContext` or `d:DesignInstance` set; designer preview shows representative data; no production logic in design-time data classes
