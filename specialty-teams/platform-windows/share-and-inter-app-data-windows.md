---
name: share-and-inter-app-data-windows
description: Implement Share Contract (`DataTransferManager`) to send and receive content; register as share target in app manifest; ...
artifact: guidelines/platform/share-and-inter-app-data.md
version: 1.0.0
---

## Worker Focus
Implement Share Contract (`DataTransferManager`) to send and receive content; register as share target in app manifest; support drag and drop via `DragDrop` APIs; register file type associations in `Package.appxmanifest` for Open With integration; support clipboard with rich content formats; validate all received data

## Verify
`DataTransferManager` used for sharing; share target declared in manifest; drag-and-drop `Drop` handler validates content; file type associations present; clipboard operations handle format availability checks
