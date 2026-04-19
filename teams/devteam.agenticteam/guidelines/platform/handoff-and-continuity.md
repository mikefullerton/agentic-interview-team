---

id: 2212a394-68d8-4588-a587-2fc637280deb
title: "Handoff and continuity"
domain: agentic-cookbook://guidelines/implementing/platform-integration/handoff-and-continuity
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-02
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Apps available on multiple devices SHOULD support continuity features so users can start work on one device and resume on another."
platforms: 
  - ios
  - macos
  - android
  - web
tags: 
  - handoff
  - continuity
  - platform
  - cross-device
depends-on: []
related:
  - agentic-cookbook://guidelines/platform/deep-linking
  - agentic-cookbook://guidelines/platform/search-integration
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - platform-integration
  - offline-support
---

# Handoff and continuity

Apps available on multiple devices SHOULD support continuity features so users can start work on one device and resume on another. Cross-device continuity reduces friction and meets the expectation that data follows the user, not the device.

- Capture enough state to reconstruct the user's context on the receiving device
- Continuity MUST feel instant — pre-transfer the minimum viable state, fetch details on arrival
- Fall back gracefully when the receiving device lacks a feature the originating device had
- Use deep links as the universal handoff payload — every platform can resolve a URL

## Apple (iOS / macOS)

Use `NSUserActivity` to advertise the current activity. Set `isEligibleForHandoff = true` and populate `userInfo` with state needed to restore context. Implement `application(_:continue:)` on the receiving device. Activities also appear in Spotlight and Siri Suggestions when `isEligibleForSearch` and `isEligibleForPrediction` are set. Support Universal Clipboard for cross-device copy/paste.

## Android

Use Google Play Services' Nearby Connections API or Chrome's cross-device features for continuity between Android devices. For Android-to-web continuity, use Firebase Dynamic Links or deep links that resolve in both native and web contexts. Support clipboard sync through Google account integration.

## Web

Use shared URLs as the primary continuity mechanism — a well-constructed URL with state parameters is the most universal handoff format. Support the Credential Management API for seamless sign-in across devices. Consider WebSocket or server-sent events for real-time state sync between active sessions.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-02 | Mike Fullerton | Initial creation |
