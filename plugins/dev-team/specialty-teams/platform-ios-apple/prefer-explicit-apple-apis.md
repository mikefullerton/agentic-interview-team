---
name: prefer-explicit-apple-apis
description: Use UIKit for all iOS UI (UICollectionViewCompositionalLayout, UINavigationController, UITextView, gesture recognizers);...
artifact: guidelines/language/swift/prefer-explicit-apple-apis.md
version: 1.0.0
---

## Worker Focus
Use UIKit for all iOS UI (UICollectionViewCompositionalLayout, UINavigationController, UITextView, gesture recognizers); use AppKit for macOS; use SwiftUI only where Apple mandates it (WidgetKit, Live Activities, App Clips); keep any mandated SwiftUI layers thin

## Verify
No SwiftUI usage outside WidgetKit/Live Activities/App Clips; UIKit used for all navigation, lists, and custom views on iOS; AppKit used for macOS equivalents; no deprecated SwiftUI navigation APIs
