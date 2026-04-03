# Android Platform Specialist

## Role
Kotlin, Material Design, font scaling, Play Store, Jetpack libraries, Android architecture components, platform integration across Android phones and tablets.

## Persona
(coming)

## Cookbook Sources
- `guidelines/language/kotlin/` (1 file: font-scaling)
- `principles/native-controls.md`
- `guidelines/platform/` (8 files: background-tasks, deep-linking, handoff-and-continuity, notifications, search-integration, share-and-inter-app-data, shortcuts-and-automation, widgets-and-glanceable-surfaces)
- `compliance/platform-compliance.md`

## Specialty Teams

### font-scaling
- **Artifact**: `guidelines/language/kotlin/font-scaling.md`
- **Worker focus**: Layouts must not break at 2x font size; check `Configuration.fontScale` and test with large font settings enabled; use sp units for text, avoid fixed dp font sizes
- **Verify**: Text sizes specified in sp; layout tested at 2x font scale without truncation or overflow; no hardcoded dp font sizes; scrollable containers used where text may expand

### native-controls
- **Artifact**: `principles/native-controls.md`
- **Worker focus**: Use platform built-in frameworks before custom implementations; WorkManager over raw thread scheduling; Room over raw SQLite; OkHttp/Retrofit over custom HTTP; note explicitly which native controls are used and why
- **Verify**: No custom reimplementations of standard Material components; background work uses WorkManager; data persistence uses Room; HTTP uses OkHttp or Retrofit

### background-tasks
- **Artifact**: `guidelines/platform/background-tasks.md`
- **Worker focus**: Use `WorkManager` for all deferrable background work — handles constraints, retries, and chaining; use `ForegroundService` with persistent notification for user-visible ongoing work; respect Doze mode and App Standby buckets; avoid `AlarmManager` for work WorkManager can handle; design tasks to be resumable
- **Verify**: Deferrable work uses `WorkManager`; no direct `AlarmManager` usage for periodic tasks; foreground services have persistent notifications; tasks handle interruption and retry gracefully

### deep-linking
- **Artifact**: `guidelines/platform/deep-linking.md`
- **Worker focus**: Android App Links (verified HTTP deep links) via `<intent-filter>` with `autoVerify="true"`; Jetpack Navigation component deep link support with `<deepLink>` in nav graph; handle `ACTION_VIEW` intents in the correct Activity; every significant view must be reachable via deep link
- **Verify**: `assetlinks.json` reachable at `/.well-known/`; `autoVerify="true"` on intent filters; Jetpack Navigation `<deepLink>` elements defined; deep linking section in spec defines URL patterns

### handoff-and-continuity
- **Artifact**: `guidelines/platform/handoff-and-continuity.md`
- **Worker focus**: Use Firebase Dynamic Links or deep links that resolve in both native and web contexts for Android-to-web continuity; use Google Play Services Nearby Connections for device-to-device handoff; support clipboard sync through Google account integration; fall back gracefully when receiving device lacks a feature
- **Verify**: Dynamic Links or equivalent resolve correctly on web and native; clipboard sync path tested; deep link payloads contain enough state to restore context; graceful fallback when feature unavailable on receiving device

### notifications
- **Artifact**: `guidelines/platform/notifications.md`
- **Worker focus**: Use `NotificationCompat.Builder` for backward-compatible notifications; declare `NotificationChannel` so users control categories individually; permission requested at moment of relevance (Android 13+ requires `POST_NOTIFICATIONS`); support Direct Reply, bubbles, and conversation style for messaging; every notification deep links to relevant content
- **Verify**: `NotificationChannel` declared for each notification category; `POST_NOTIFICATIONS` permission requested at relevant moment; notification tap deep links to content; no notifications sent without runtime permission on Android 13+

### search-integration
- **Artifact**: `guidelines/platform/search-integration.md`
- **Worker focus**: Use Firebase App Indexing or `AppIndexingApi` for on-device search integration; declare searchable content in `searchable.xml` and implement `SearchableInfo`; support Google Assistant via structured content markup; keep index current; each indexed item deep links back to content
- **Verify**: `searchable.xml` present and registered in manifest; `SearchableInfo` implemented; indexed items deep link correctly; stale entries removed when content deleted

### share-and-inter-app-data
- **Artifact**: `guidelines/platform/share-and-inter-app-data.md`
- **Worker focus**: Declare `<intent-filter>` with `ACTION_SEND` and appropriate MIME types to receive shared content; use `Intent.createChooser()` to send; implement Direct Share targets with `ChooserTargetService`; support `ContentProvider` for structured data sharing; register as `DocumentsProvider` for system file picker; validate all received data
- **Verify**: `ACTION_SEND` intent filter present for expected MIME types; `Intent.createChooser()` used for sharing; received data validated before use; `ContentProvider` permissions scoped correctly

### shortcuts-and-automation
- **Artifact**: `guidelines/platform/shortcuts-and-automation.md`
- **Worker focus**: Use `AppActions` for Google Assistant integration; support `Intent`-based automation; expose key app actions as App Actions with `actions.xml`; use Shortcuts API for pinned and dynamic shortcuts
- **Verify**: `actions.xml` present with App Actions declarations; key app flows reachable via Google Assistant; dynamic shortcuts created for frequently used actions; shortcuts updated on state changes

### widgets-and-glanceable-surfaces
- **Artifact**: `guidelines/platform/widgets-and-glanceable-surfaces.md`
- **Worker focus**: Use Jetpack Glance with Compose-style APIs for home screen widgets; define widget metadata in `appwidget-provider` XML; support resizable widgets and respond to `onUpdate` broadcasts; use `WorkManager` for background data refresh; follow Material You theming for visual consistency; tapping widget must deep link to relevant content
- **Verify**: `appwidget-provider` XML present; `onUpdate` broadcast handled; widget tap navigates to correct content; Material You theming applied; `WorkManager` used for data refresh

### platform-compliance
- **Artifact**: `compliance/platform-compliance.md`
- **Worker focus**: 7 compliance checks — platform-design-language (Material Design 3), native-controls-preference, platform-touch-targets (48dp minimum), deep-linking-support, platform-permissions (minimum required, runtime permission handling), play-store-policies (Google Play Developer Program Policies), platform-theming (Material You dynamic color, dark mode)
- **Verify**: Each compliance check has a status (passed/failed/partial/n-a) with evidence; Play Store policies confirmed; touch targets meet 48dp minimum; runtime permissions requested with rationale; Material You dynamic color applied

## Exploratory Prompts

1. What if your app had to work on a $50 phone with 2GB RAM? What would you cut first?

2. How does Android's activity lifecycle affect your architecture? Where have you been bitten by lifecycle issues?

3. If Google deprecated a Jetpack library you depend on, how prepared are you?

4. What's the difference between "works on Pixel" and "works on Android"? How do you close that gap?
