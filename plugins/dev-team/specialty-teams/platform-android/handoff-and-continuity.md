---
name: handoff-and-continuity
description: Use Firebase Dynamic Links or deep links that resolve in both native and web contexts for Android-to-web continuity; use...
artifact: guidelines/platform/handoff-and-continuity.md
version: 1.0.0
---

## Worker Focus
Use Firebase Dynamic Links or deep links that resolve in both native and web contexts for Android-to-web continuity; use Google Play Services Nearby Connections for device-to-device handoff; support clipboard sync through Google account integration; fall back gracefully when receiving device lacks a feature

## Verify
Dynamic Links or equivalent resolve correctly on web and native; clipboard sync path tested; deep link payloads contain enough state to restore context; graceful fallback when feature unavailable on receiving device
