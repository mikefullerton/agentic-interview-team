---

id: 193e5770-fd0b-45c9-91a4-6673bf6021ff
title: "Share and inter-app data flow"
domain: agentic-cookbook://guidelines/implementing/platform-integration/share-and-inter-app-data
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-02
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Apps SHOULD participate in the platform's share and inter-app data exchange mechanisms to integrate with other apps and workflows."
platforms: 
  - ios
  - macos
  - android
  - windows
  - web
tags: 
  - sharing
  - platform
  - inter-app
  - drag-and-drop
depends-on:
  - agentic-cookbook://principles/support-automation
related:
  - agentic-cookbook://guidelines/platform/deep-linking
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - platform-integration
---

# Share and inter-app data flow

Apps SHOULD participate in the platform's share and inter-app data exchange mechanisms to integrate with other apps and workflows. Users expect to move data between apps without friction.

- Support both sending and receiving data through the platform share sheet
- Register as a handler for relevant file types and UTIs/MIME types
- Support drag and drop for content that makes sense in multi-window contexts
- Validate all received data — inter-app data is an untrusted input boundary

## Apple (iOS / macOS)

Implement `UIActivityViewController` (iOS) or `NSSharingServicePicker` (macOS) to share content. Create Share Extensions to receive content from other apps. Register UTI declarations in `Info.plist` for file type associations. Support drag and drop via `NSItemProvider` on iPadOS and macOS. On macOS, support the Services menu via `NSServices` for system-wide text operations.

## Android

Declare `<intent-filter>` with `ACTION_SEND` and appropriate MIME types to receive shared content. Use `Intent.createChooser()` to send. Implement Direct Share targets with `ChooserTargetService` for frequently shared-to contacts. Support `ContentProvider` for structured data sharing between apps. Register as a document provider via `DocumentsProvider` for the system file picker.

## Windows

Implement the Share Contract (`DataTransferManager`) to send and receive content. Register as a share target in the app manifest. Support drag and drop via `DragDrop` APIs. Register file type associations in `Package.appxmanifest` for Open With integration. Support clipboard with rich content formats.

## Web

Use the Web Share API (`navigator.share()`) to invoke the native share sheet. Register as a share target in the Web App Manifest (`share_target`). Support drag and drop via the HTML Drag and Drop API. Use the File Handling API to register as a handler for specific file types in PWAs.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-02 | Mike Fullerton | Initial creation |
