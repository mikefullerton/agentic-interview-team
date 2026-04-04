---
name: share-and-inter-app-data
description: Use `UIActivityViewController` (iOS) or `NSSharingServicePicker` (macOS) to share content; create Share Extensions to re...
artifact: guidelines/platform/share-and-inter-app-data.md
version: 1.0.0
---

## Worker Focus
Use `UIActivityViewController` (iOS) or `NSSharingServicePicker` (macOS) to share content; create Share Extensions to receive content from other apps; register UTI declarations in `Info.plist`; support drag and drop via `NSItemProvider` on iPadOS/macOS; on macOS support Services menu via `NSServices`

## Verify
Share sheet invoked via `UIActivityViewController`; Share Extension handles expected content types; UTI declarations present in `Info.plist`; received data validated before use
