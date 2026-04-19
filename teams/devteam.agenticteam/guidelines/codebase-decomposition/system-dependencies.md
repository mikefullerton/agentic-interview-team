---

id: 03539f34-3451-49d5-b90f-ba77430f2658
title: "System Dependencies"
domain: agentic-cookbook://guidelines/planning/code-quality/system-dependencies
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Characterize which external libraries, OS frameworks, and system services the code reaches for, and what that implies about scope boundaries."
platforms:
  - csharp
  - ios
  - kotlin
  - typescript
  - web
  - windows
tags:
  - codebase-decomposition
depends-on: []
related: []
references: []
triggers:
  - new-module
  - dependency-management
---

# System Dependencies

Code that reaches into an OS framework, hardware API, or external service is fundamentally different from code that operates only on its own data. System dependencies reveal the technical surface area of a scope group — what the host platform must provide, what permissions are implied, and what cannot be easily mocked or isolated. This lens catalogs every external system the code touches to characterize the integration profile of each candidate scope group.

## Signals and Indicators

**OS and platform framework imports:**

- iOS/macOS: `UIKit`, `AppKit`, `SwiftUI`, `CoreData`, `CoreLocation`, `CoreMotion`, `AVFoundation`, `ARKit`, `HealthKit`, `HomeKit`, `MapKit`, `StoreKit`, `UserNotifications`, `LocalAuthentication`, `CryptoKit`, `Network`, `Combine`
- Android/Kotlin: `android.hardware.*`, `android.location.*`, `android.media.*`, `android.bluetooth.*`, `android.nfc.*`, `android.telephony.*`, `com.google.android.gms.*` (Google Play Services), `androidx.camera.*`, `androidx.biometric.*`
- Windows: `Windows.UI.*`, `Windows.Devices.*`, `Windows.Media.*`, `Windows.Storage.*`, `Windows.Security.*`, `Windows.Networking.*`, `System.IO.*`, `System.Net.*`, `System.Security.*`
- Web: `navigator.geolocation`, `navigator.mediaDevices`, `navigator.bluetooth`, `window.indexedDB`, `window.localStorage`, `window.sessionStorage`, `ServiceWorker`, `WebSockets`, `WebRTC`, `WebGL`, `WebAssembly`
- C#: `System.IO`, `System.Net`, `System.Security.Cryptography`, `System.Runtime.InteropServices`, `Microsoft.Win32`

**Hardware access APIs:**

- Camera: `AVCaptureSession` (iOS), `CameraX` (Android), `MediaDevices.getUserMedia()` (Web), `Windows.Media.Capture`
- GPS/Location: `CLLocationManager` (iOS), `FusedLocationProviderClient` (Android), `Geolocation API` (Web), `Windows.Devices.Geolocation`
- Bluetooth: `CoreBluetooth` (iOS), `android.bluetooth` (Android), `Web Bluetooth API`, `Windows.Devices.Bluetooth`
- Biometrics: `LocalAuthentication` (iOS), `BiometricPrompt` (Android), `WebAuthn` (Web), `Windows.Security.Credentials`
- Sensors: `CoreMotion` (iOS), `SensorManager` (Android), `DeviceMotionEvent` (Web)

**System service calls:**

- Keychain/Credential storage: `SecItemAdd/SecItemCopyMatching` (iOS/macOS), `EncryptedSharedPreferences` (Android), `Windows.Security.Credentials.PasswordVault`, Web Credentials Management API
- File system: Direct `FileManager` usage (iOS), `java.io.File` (Android/JVM), `System.IO.File` (C#), `fs` module (Node.js), `File System Access API` (Web)
- Network stack: `URLSession` (iOS), `OkHttp`/`Retrofit` (Android), `HttpClient` (C#), `fetch`/`XMLHttpRequest` (Web), `axios`/`node-fetch` (Node.js)
- Push notifications: `UNUserNotificationCenter` (iOS), `FirebaseMessaging` (Android), Web Push API
- In-app purchases: `StoreKit` (iOS), `BillingClient` (Android), Web Payments API

**Third-party SDK usage:**

- Analytics: Firebase Analytics, Mixpanel, Amplitude, Segment, AppsFlyer
- Crash reporting: Crashlytics, Sentry, Bugsnag
- Maps: Google Maps SDK, Mapbox, Apple MapKit
- Payments: Stripe SDK, Braintree, Square
- Authentication: Auth0 SDK, Firebase Auth, Okta
- Database: Realm, SQLite (direct), Room (Android), Core Data (iOS)

## Boundary Detection

1. **Heavy OS framework usage marks a boundary.** Files that import three or more OS-specific frameworks are tightly coupled to the platform runtime and likely belong in a platform-specific scope group.
2. **Hardware APIs are natural boundaries.** Camera, GPS, Bluetooth, and biometric code has distinct permission requirements and testing needs — group these files together and mark the scope group as hardware-dependent.
3. **Network and persistence are separate concerns.** Files that talk to the network and files that write to local storage are often conflated — separate them unless they are part of a unified data synchronization layer.
4. **Third-party SDK boundaries.** If a third-party SDK is touched by more than 2–3 files, those files likely form a wrapper/adapter scope group that isolates the SDK from the rest of the codebase. Identify this group explicitly.
5. **System dependencies that appear in many groups are cross-cutting.** Logging frameworks and analytics SDKs that appear across all candidate groups are not boundaries — they are cross-cutting concerns (see `cross-cutting-detection`).

## Findings Format

```
SYSTEM DEPENDENCIES FINDINGS
=============================

OS/Platform Frameworks Used:
  - <FrameworkName> — used in <n> files: <file list or representative sample>

Hardware APIs:
  - <API> (<capability>) — files: <list>

System Services:
  - <Service> (<purpose>) — files: <list>

Third-Party SDKs:
  - <SDK Name> (<vendor>, <category>) — used in <n> files: <file list>

Dependency Profile by Directory/Candidate Group:
  - <Directory>: <dominant framework(s)>, <hardware APIs if any>, <third-party SDKs>

Cross-Cutting System Dependencies (appear in 3+ candidate groups):
  - <Dependency> — consider abstracting behind an interface

Recommended Scope Group Candidates:
  - <Name> — <primary system dependency>, <one-line rationale>
```

## Change History
