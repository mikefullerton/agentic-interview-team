---
name: deep-linking
description: Android App Links (verified HTTP deep links) via `<intent-filter>` with `autoVerify="true"`; Jetpack Navigation componen...
artifact: guidelines/platform/deep-linking.md
version: 1.0.0
---

## Worker Focus
Android App Links (verified HTTP deep links) via `<intent-filter>` with `autoVerify="true"`; Jetpack Navigation component deep link support with `<deepLink>` in nav graph; handle `ACTION_VIEW` intents in the correct Activity; every significant view must be reachable via deep link

## Verify
`assetlinks.json` reachable at `/.well-known/`; `autoVerify="true"` on intent filters; Jetpack Navigation `<deepLink>` elements defined; deep linking section in spec defines URL patterns
