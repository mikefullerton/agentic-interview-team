---

id: 095b33a1-2835-4ed5-bf01-f1e492148819
title: "Use AppKit and UIKit, not SwiftUI"
domain: agentic-cookbook://guidelines/implementing/platform-integration/prefer-explicit-apple-apis
type: guideline
version: 2.0.2
status: accepted
language: en
created: 2026-04-02
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Use AppKit (macOS) and UIKit (iOS) for all UI. Use SwiftUI only where Apple requires it."
platforms: 
  - ios
  - macos
languages:
  - swift
tags: 
  - swift
  - appkit
  - uikit
  - swiftui
  - agentic
depends-on:
  - agentic-cookbook://principles/native-controls
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - platform-integration
  - ui-implementation
---

# Use AppKit and UIKit, not SwiftUI

AppKit (macOS) and UIKit (iOS) MUST be used for all UI code. SwiftUI MUST only be used where Apple requires it (widgets, Live Activities, App Clips). SwiftUI exists to make writing UI code easier for humans — agentic development doesn't need that. Go straight to the best tool for the LLM.

- SwiftUI is a convenience layer designed for human ergonomics: less boilerplate, live previews, reduced cognitive load. An LLM has none of these needs.
- AppKit/UIKit have 15+ years of training data, stable APIs, and explicit imperative patterns that LLMs generate reliably
- SwiftUI's API churn (NavigationView → NavigationStack, @ObservedObject → @Observable) causes version-specific generation errors that waste debugging cycles
- SwiftUI's implicit behavior (modifier ordering, view diffing, opaque layout resolution) creates bugs that are hard for agents to diagnose
- Cross-platform code sharing between iOS and macOS via SwiftUI is a compromise — the cookbook's philosophy is native code per platform, not cross-platform abstraction

## macOS

Use AppKit. `NSTableView`, `NSSplitViewController`, `NSWindow`, `NSMenu`, custom drawing via `NSView.draw(_:)` — AppKit provides explicit control over cell reuse, view recycling, responder chain, and rendering. Every behavior is visible and predictable.

## iOS

Use UIKit. `UICollectionViewCompositionalLayout`, `UINavigationController`, `UITextView` with TextKit 2, gesture recognizers, view controller containment — UIKit's imperative model means every step is an explicit instruction an LLM can follow and debug.

## When SwiftUI is required

Apple mandates SwiftUI for certain surfaces. Use it only there:
- **WidgetKit** extensions (home screen and lock screen widgets)
- **Live Activities** and Dynamic Island presentations
- **App Clips** (SwiftUI is strongly recommended by Apple)

In these cases, the SwiftUI layer SHOULD be kept as thin as possible. Pin the minimum deployment target and avoid deprecated APIs to reduce generation ambiguity.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 2.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 2.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-02 | Mike Fullerton | Initial creation |
| 2.0.0 | 2026-04-02 | Mike Fullerton | Strengthen position: use AppKit/UIKit for all UI, SwiftUI only when required by Apple |
