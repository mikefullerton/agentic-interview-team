---
name: deep-linking
description: Universal Links for HTTP-based deep links with associated domain entitlement; custom URL schemes as fallback; `onOpenURL...
artifact: guidelines/platform/deep-linking.md
version: 1.0.0
---

## Worker Focus
Universal Links for HTTP-based deep links with associated domain entitlement; custom URL schemes as fallback; `onOpenURL` in SwiftUI or `application(_:open:)` in UIKit; `NavigationPath` for state restoration; every significant view must be reachable via deep link

## Verify
Associated domains entitlement present; `apple-app-site-association` file reachable; deep link handler navigates to correct content; deep linking section in spec defines URL patterns
