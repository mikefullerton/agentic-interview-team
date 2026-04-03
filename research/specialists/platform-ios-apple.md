# iOS / Apple Platforms Specialist

## Role
UIKit, AppKit, SwiftUI (where Apple requires it), Dynamic Type, App Store, Human Interface Guidelines, platform integration across iOS, macOS, watchOS, tvOS, and visionOS.

## Persona
(coming)

## Cookbook Sources
- `guidelines/language/swift/` (2 files)
- `principles/native-controls.md`
- `guidelines/platform/` (8 files: background-tasks, deep-linking, handoff-and-continuity, notifications, search-integration, share-and-inter-app-data, shortcuts-and-automation, widgets-and-glanceable-surfaces)
- `compliance/platform-compliance.md`

## Specialty Teams

### dynamic-type
- **Artifact**: `guidelines/language/swift/dynamic-type.md`
- **Worker focus**: Layouts must not break at larger text sizes; use Dynamic Type throughout with no fixed font sizes; custom fonts must respond to the bold text accessibility setting
- **Verify**: No hardcoded font sizes; all text uses Dynamic Type scale; layout tested at Extra Large and Accessibility Extra Extra Extra Large sizes; bold text setting respected

### prefer-explicit-apple-apis
- **Artifact**: `guidelines/language/swift/prefer-explicit-apple-apis.md`
- **Worker focus**: Use UIKit for all iOS UI (UICollectionViewCompositionalLayout, UINavigationController, UITextView, gesture recognizers); use AppKit for macOS; use SwiftUI only where Apple mandates it (WidgetKit, Live Activities, App Clips); keep any mandated SwiftUI layers thin
- **Verify**: No SwiftUI usage outside WidgetKit/Live Activities/App Clips; UIKit used for all navigation, lists, and custom views on iOS; AppKit used for macOS equivalents; no deprecated SwiftUI navigation APIs

### native-controls
- **Artifact**: `principles/native-controls.md`
- **Worker focus**: Use platform built-in frameworks before custom implementations; Swift Concurrency over raw threads; SwiftData/Core Data over raw SQLite; URLSession over custom HTTP; note explicitly which native controls are used and why
- **Verify**: No custom reimplementations of standard iOS controls; concurrency uses async/await or Actors; data persistence uses SwiftData or Core Data; HTTP uses URLSession

### background-tasks
- **Artifact**: `guidelines/platform/background-tasks.md`
- **Worker focus**: Use `BGAppRefreshTask` and `BGProcessingTask` via BackgroundTasks framework for deferred work; use `URLSession` background transfers for uploads/downloads that survive suspension; on macOS use `ProcessInfo.performActivity` and `NSBackgroundActivityScheduler`; design tasks to be resumable
- **Verify**: No foreground-only sync logic; `BGAppRefreshTask`/`BGProcessingTask` registered and handled; `URLSession` background configuration used for transfers; tasks handle interruption gracefully

### deep-linking
- **Artifact**: `guidelines/platform/deep-linking.md`
- **Worker focus**: Universal Links for HTTP-based deep links with associated domain entitlement; custom URL schemes as fallback; `onOpenURL` in SwiftUI or `application(_:open:)` in UIKit; `NavigationPath` for state restoration; every significant view must be reachable via deep link
- **Verify**: Associated domains entitlement present; `apple-app-site-association` file reachable; deep link handler navigates to correct content; deep linking section in spec defines URL patterns

### handoff-and-continuity
- **Artifact**: `guidelines/platform/handoff-and-continuity.md`
- **Worker focus**: Use `NSUserActivity` to advertise current activity with `isEligibleForHandoff = true`; populate `userInfo` with minimal state to restore context; implement `application(_:continue:)` on receiving device; set `isEligibleForSearch` and `isEligibleForPrediction` for Spotlight and Siri Suggestions; support Universal Clipboard
- **Verify**: `NSUserActivity` created and updated for eligible screens; `userInfo` contains enough state to restore; receiving handler implemented; `isEligibleForHandoff` set correctly

### notifications
- **Artifact**: `guidelines/platform/notifications.md`
- **Worker focus**: Use `UNUserNotificationCenter` for local and push notifications; permission requested at moment of relevance, not at launch; support `UNNotificationCategory` and `UNNotificationAction` for actionable notifications; every notification deep links to relevant content; respect iOS interruption levels (Time Sensitive, Notification Summary)
- **Verify**: Permission request deferred to relevant moment; `UNNotificationCategory` registered with actions; notification tap deep links to content; no notifications sent without user permission

### search-integration
- **Artifact**: `guidelines/platform/search-integration.md`
- **Worker focus**: Use Core Spotlight (`CSSearchableItem`, `CSSearchableItemAttributeSet`) to index content; on iOS 17+ use `IndexedEntity` for semantic indexing; donate `NSUserActivity` for Handoff-eligible items to appear in Spotlight suggestions; keep index current (add on create, remove on delete); each indexed item must deep link back to content
- **Verify**: `CSSearchableItemAttributeSet` populated with title, description, thumbnail; indexed items deep link correctly; stale items removed when content deleted; `NSUserActivity` donated for key screens

### share-and-inter-app-data
- **Artifact**: `guidelines/platform/share-and-inter-app-data.md`
- **Worker focus**: Use `UIActivityViewController` (iOS) or `NSSharingServicePicker` (macOS) to share content; create Share Extensions to receive content from other apps; register UTI declarations in `Info.plist`; support drag and drop via `NSItemProvider` on iPadOS/macOS; on macOS support Services menu via `NSServices`
- **Verify**: Share sheet invoked via `UIActivityViewController`; Share Extension handles expected content types; UTI declarations present in `Info.plist`; received data validated before use

### shortcuts-and-automation
- **Artifact**: `guidelines/platform/shortcuts-and-automation.md`
- **Worker focus**: Use `AppIntents` framework for Shortcuts and Siri integration on iOS and macOS; on macOS support AppleScript via `NSScriptCommand` where appropriate; expose key app actions as intents; provide parameter summaries and suggested phrases
- **Verify**: `AppIntent` conformances present for key actions; intents appear in Shortcuts app; on macOS, scriptable actions documented; parameter types use standard types where possible

### widgets-and-glanceable-surfaces
- **Artifact**: `guidelines/platform/widgets-and-glanceable-surfaces.md`
- **Worker focus**: Use WidgetKit with SwiftUI views (one of the mandated SwiftUI surfaces); support small, medium, and large families; on iOS 17+ support interactive widgets with `AppIntent`-backed buttons; on iOS 16+ support Lock Screen widgets; use `TimelineProvider` for scheduled updates; tapping widget must deep link to relevant content; use `ActivityKit` for Live Activities with Dynamic Island
- **Verify**: Widget supports at least small and medium families; `TimelineProvider` implemented; widget tap navigates to correct content; interactive widget actions backed by `AppIntent`; no SwiftUI deprecated navigation APIs in widget

### platform-compliance
- **Artifact**: `compliance/platform-compliance.md`
- **Worker focus**: 7 compliance checks — platform-design-language (HIG), native-controls-preference, platform-touch-targets (44pt minimum), deep-linking-support, platform-permissions (minimum required), app-store-guidelines (Apple Review Guidelines), platform-theming (dark mode, Dynamic Type)
- **Verify**: Each compliance check has a status (passed/failed/partial/n-a) with evidence; App Store guidelines confirmed; touch targets meet 44pt minimum; theming adapts to system appearance

## Exploratory Prompts

1. Why does Apple care so much about Dynamic Type? What's the deeper accessibility principle?

2. What if you had to support VoiceOver from the start? How would that change your design process?

3. If your app had to adapt to any screen size (iPhone, iPad, Mac), what's the core experience that never changes?

4. When do you follow HIG conventions, and when do you break them? What earns a deviation?
