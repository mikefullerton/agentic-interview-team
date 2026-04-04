---
name: rtl-support
description: Leading/trailing (not left/right) for all alignment and padding; directional icons mirrored; non-directional icons not m...
artifact: guidelines/internationalization/rtl-support.md
version: 1.0.0
---

## Worker Focus
Leading/trailing (not left/right) for all alignment and padding; directional icons mirrored; non-directional icons not mirrored; `android:supportsRtl="true"` on Android, CSS logical properties on web, `FlowDirection` on Windows; RTL locale tested

## Verify
No `left`/`right` layout constraints or CSS properties — only leading/trailing/logical equivalents; `supportsRtl` manifest flag set on Android; directional icons have RTL variants; RTL locale tested in preview or emulator
