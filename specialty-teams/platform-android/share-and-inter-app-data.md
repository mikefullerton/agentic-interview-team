---
name: share-and-inter-app-data
description: Declare `<intent-filter>` with `ACTION_SEND` and appropriate MIME types to receive shared content; use `Intent.createCho...
artifact: guidelines/platform/share-and-inter-app-data.md
version: 1.0.0
---

## Worker Focus
Declare `<intent-filter>` with `ACTION_SEND` and appropriate MIME types to receive shared content; use `Intent.createChooser()` to send; implement Direct Share targets with `ChooserTargetService`; support `ContentProvider` for structured data sharing; register as `DocumentsProvider` for system file picker; validate all received data

## Verify
`ACTION_SEND` intent filter present for expected MIME types; `Intent.createChooser()` used for sharing; received data validated before use; `ContentProvider` permissions scoped correctly
