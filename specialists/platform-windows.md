# Windows Platform Specialist

## Role
WinUI 3, Fluent Design, MSIX packaging, High DPI/display scaling, MVVM with CommunityToolkit, theming (light/dark/high-contrast), .NET/C#, Narrator, UI Automation, platform integration.

## Persona
(coming)

## Cookbook Sources
- `guidelines/platform/windows/` (6 files: architecture, design-time-data, fluent-design, high-dpi-display-scaling, msix-packaging, theming)
- `guidelines/language/csharp/` (3 files: dependency-injection, naming, nullable-reference-types)
- `principles/native-controls.md`
- `guidelines/platform/` (8 files: background-tasks, deep-linking, handoff-and-continuity, notifications, search-integration, share-and-inter-app-data, shortcuts-and-automation, widgets-and-glanceable-surfaces)
- `compliance/platform-compliance.md`

## Specialty Teams

### windows-architecture
- **Artifact**: `guidelines/platform/windows/architecture.md`
- **Worker focus**: MVVM with CommunityToolkit.Mvvm — source-generated `ObservableObject`, `RelayCommand`, and messaging; NavigationView + Frame for page-level navigation; navigation service abstraction in ViewModel layer (never manipulate Frame from code-behind); use Template Studio for project scaffolding
- **Verify**: `[ObservableObject]` and `[RelayCommand]` source generators used; no Frame manipulation in code-behind; navigation service interface injected into ViewModels; `INotifyPropertyChanged` not hand-implemented

### design-time-data
- **Artifact**: `guidelines/platform/windows/design-time-data.md`
- **Worker focus**: Use `d:DataContext` and `d:DesignInstance` for XAML designer preview data; use XAML Hot Reload for live iteration during development; keep design-time data classes lightweight and separate from production code
- **Verify**: XAML views have `d:DataContext` or `d:DesignInstance` set; designer preview shows representative data; no production logic in design-time data classes

### fluent-design
- **Artifact**: `guidelines/platform/windows/fluent-design.md`
- **Worker focus**: Use built-in WinUI 3 controls — they implement Fluent 2 natively; never custom-draw what a standard control can do; use Segoe UI Variable for typography; use Segoe Fluent Icons for iconography; follow Windows design guidance for layout, spacing, and navigation patterns
- **Verify**: No custom-drawn controls where standard WinUI 3 equivalents exist; Segoe UI Variable used for text; Segoe Fluent Icons used for icons; layout follows Windows spacing and navigation patterns

### high-dpi-display-scaling
- **Artifact**: `guidelines/platform/windows/high-dpi-display-scaling.md`
- **Worker focus**: XAML layout uses effective pixels (epx) — scaling is automatic for XAML content; provide bitmap assets at multiple scales (.scale-100, .scale-125, .scale-150, .scale-200, .scale-400); for custom rendering (Win2D, Direct3D) query `XamlRoot.RasterizationScale` and listen for `RasterizationScaleChanged`; never hard-code pixel sizes in code-behind
- **Verify**: No hard-coded pixel sizes in code-behind; bitmap assets present at all required scale suffixes; custom rendering handlers subscribe to `RasterizationScaleChanged`; layout tested at 100%, 150%, and 200% DPI

### msix-packaging
- **Artifact**: `guidelines/platform/windows/msix-packaging.md`
- **Worker focus**: Use single-project MSIX packaging model; declare capabilities minimally in `Package.appxmanifest`; sign packages with a trusted certificate for sideloading; version numbering follows `Major.Minor.Build.Revision` monotonically increasing scheme
- **Verify**: Single-project packaging model used; only required capabilities declared in manifest; package signed with certificate; version number monotonically increases across releases

### theming
- **Artifact**: `guidelines/platform/windows/theming.md`
- **Worker focus**: WinUI 3 tri-state theming — Light, Dark, High Contrast; set app-level theme via `Application.RequestedTheme`; always use `ThemeResource` (not `StaticResource`) for colors and brushes to enable runtime switching; use semantic color resources (`TextFillColorPrimary`, `CardBackgroundFillColorDefault`) not hex values; define custom theme-aware colors in `ResourceDictionary` with Default/Light/Dark dictionaries
- **Verify**: No hex color values in XAML; `ThemeResource` used exclusively for colors and brushes; app renders correctly in Light, Dark, and High Contrast modes; custom colors defined with theme dictionary variants

### dependency-injection
- **Artifact**: `guidelines/language/csharp/dependency-injection.md`
- **Worker focus**: Constructor injection via `Microsoft.Extensions.DependencyInjection`; use interface types for dependencies (not concrete types); `Transient` for stateless services, `Scoped` for per-request, `Singleton` for thread-safe shared state; no scoped service injected into singleton (captive dependency); use `IOptions<T>` / `IOptionsSnapshot<T>` for configuration; registrations in `Add*()` extension methods
- **Verify**: All dependencies injected via constructor with interface types; no captive dependencies (scoped in singleton); `IOptions<T>` used for configuration binding; service registrations in extension methods

### csharp-naming
- **Artifact**: `guidelines/language/csharp/naming.md`
- **Worker focus**: PascalCase for types, methods, properties, public fields, constants, namespaces; camelCase for parameters and local variables; `_camelCase` (underscore prefix) for private instance fields; `I` prefix for interfaces; `Async` suffix for async methods; constants use PascalCase not SCREAMING_SNAKE_CASE; use `var` when type is apparent
- **Verify**: Private fields use `_camelCase`; interfaces prefixed with `I`; async methods suffixed with `Async`; no `SCREAMING_SNAKE_CASE` constants; consistent PascalCase on public members

### nullable-reference-types
- **Artifact**: `guidelines/language/csharp/nullable-reference-types.md`
- **Worker focus**: Enable `<Nullable>enable</Nullable>` in all projects; treat warnings as design signals — `string` means non-null, `string?` means nullable; avoid null-forgiving operator (`!`) — prefer `?? throw` or guard clauses; use `required` properties and constructor parameters for non-null initialization; use `[NotNull]`, `[MaybeNull]`, `[NotNullWhen]` for contracts compiler cannot infer
- **Verify**: `<Nullable>enable</Nullable>` in all `.csproj` files; no null-forgiving operator (`!`) usage; non-null properties use `required`; `ArgumentNullException.ThrowIfNull` used at entry points; zero nullable warnings

### native-controls
- **Artifact**: `principles/native-controls.md`
- **Worker focus**: Use platform built-in frameworks before custom implementations; WinUI 3 controls over custom-drawn equivalents; Windows App SDK APIs for system integration; note explicitly which native controls are used and why; if ambiguity exists about native control fit, ask before proceeding
- **Verify**: No custom reimplementations of standard WinUI 3 controls; system APIs used for file access, notifications, and background tasks; deviations from native controls documented with rationale

### background-tasks
- **Artifact**: `guidelines/platform/background-tasks.md`
- **Worker focus**: Use `BackgroundTask` with Windows App SDK for background execution; register triggers (time, network state change, push notification) in app manifest; for long-running tasks use `ExtendedExecutionSession`; background tasks in MSIX run in separate process with limited resource access; design tasks to be resumable
- **Verify**: Background task triggers declared in `Package.appxmanifest`; `ExtendedExecutionSession` used for long-running operations; tasks handle interruption and restart gracefully; no reliance on foreground presence for critical sync

### deep-linking
- **Artifact**: `guidelines/platform/deep-linking.md`
- **Worker focus**: Protocol activation via `<uap:Protocol>` declaration in `Package.appxmanifest`; handle activation through `AppInstance.GetActivatedEventArgs()` in `App.OnLaunched`; use `AppInstance.FindOrRegisterForKey()` for single-instancing; parse URI to determine target page/state and navigate accordingly; every significant view must be reachable via protocol activation
- **Verify**: `<uap:Protocol>` declared in manifest; `AppInstance.GetActivatedEventArgs()` handled in `OnLaunched`; URI parsed to navigate to correct page; single-instancing implemented; deep linking section in spec defines URI patterns

### notifications-windows
- **Artifact**: `guidelines/platform/notifications.md`
- **Worker focus**: Use `AppNotificationManager` + `AppNotificationBuilder` fluent API for local notifications; support text, images, buttons with activation arguments, progress bars, and scheduled delivery; handle notification activation alongside protocol activation; MSIX-packaged apps get notification identity automatically; request permission at moment of relevance
- **Verify**: `AppNotificationManager` used (not legacy toast APIs); activation arguments handled in `OnLaunched`; notification tap navigates to relevant content; scheduled notifications use correct delivery time; no notifications sent before permission granted

### search-integration-windows
- **Artifact**: `guidelines/platform/search-integration.md`
- **Worker focus**: Use Windows Search indexer with `ISearchManager` and property handlers; register file type associations and protocol handlers so content appears in Start menu search; for WinUI, use in-app search with system integration via `SearchPane` or equivalent; keep index current; each indexed item deep links back to content
- **Verify**: File type associations registered in manifest; property handlers deployed for custom file types; indexed items resolve via protocol activation; search results navigate to correct content

### share-and-inter-app-data-windows
- **Artifact**: `guidelines/platform/share-and-inter-app-data.md`
- **Worker focus**: Implement Share Contract (`DataTransferManager`) to send and receive content; register as share target in app manifest; support drag and drop via `DragDrop` APIs; register file type associations in `Package.appxmanifest` for Open With integration; support clipboard with rich content formats; validate all received data
- **Verify**: `DataTransferManager` used for sharing; share target declared in manifest; drag-and-drop `Drop` handler validates content; file type associations present; clipboard operations handle format availability checks

### shortcuts-and-automation-windows
- **Artifact**: `guidelines/platform/shortcuts-and-automation.md`
- **Worker focus**: Protocol activation for automation entry points; command-line activation via `AppInstance` APIs; WinUI 3 has limited scripting support compared to other platforms — document what automation is available; expose key flows via protocol activation URIs
- **Verify**: Protocol activation URIs documented; command-line activation handled if supported; automation entry points tested; limitations of WinUI 3 scripting acknowledged in docs

### handoff-and-continuity-windows
- **Artifact**: `guidelines/platform/handoff-and-continuity.md`
- **Worker focus**: Windows does not have a native Handoff equivalent — use deep links as universal handoff payload; protocol activation URIs as cross-device handoff mechanism; fall back gracefully when receiving device lacks a feature; web-resolvable URLs for cross-platform continuity
- **Verify**: Key views have protocol activation URIs suitable for cross-device handoff; URLs resolve on web or mobile equivalents; state encoded in URI is sufficient to restore context

### platform-compliance
- **Artifact**: `compliance/platform-compliance.md`
- **Worker focus**: 7 compliance checks — platform-design-language (Fluent Design), native-controls-preference (WinUI 3 controls), platform-touch-targets (touch targets for touch-enabled Windows devices), deep-linking-support (protocol activation), platform-permissions (minimal capabilities in manifest), platform-theming (light/dark/high-contrast), no app-store check applies unless targeting Microsoft Store
- **Verify**: Each compliance check has a status (passed/failed/partial/n-a) with evidence; Fluent Design confirmed; WinUI 3 controls used; theming covers all three modes; only required capabilities declared

## Exploratory Prompts

1. Why does Fluent Design emphasize simplicity and focus? What assumptions about desktop apps is that challenging?

2. What if you had to support every DPI from 96 to 500 without custom pixel fiddling? How would you think about scaling?

3. If nullable reference types are enabled, what does that tell you about the code's intent?

4. Why is "use TextFillColorPrimary" better than "use #FFFFFF"? What's the relationship between semantic colors and maintainability?
