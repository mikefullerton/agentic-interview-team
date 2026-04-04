---
name: handoff-and-continuity
description: Use `NSUserActivity` to advertise current activity with `isEligibleForHandoff = true`; populate `userInfo` with minimal ...
artifact: guidelines/platform/handoff-and-continuity.md
version: 1.0.0
---

## Worker Focus
Use `NSUserActivity` to advertise current activity with `isEligibleForHandoff = true`; populate `userInfo` with minimal state to restore context; implement `application(_:continue:)` on receiving device; set `isEligibleForSearch` and `isEligibleForPrediction` for Spotlight and Siri Suggestions; support Universal Clipboard

## Verify
`NSUserActivity` created and updated for eligible screens; `userInfo` contains enough state to restore; receiving handler implemented; `isEligibleForHandoff` set correctly
