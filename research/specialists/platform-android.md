# Android Platform Specialist

## Domain Coverage
Kotlin, Material Design, font scaling, Play Store, Jetpack Compose, Android architecture components, platform integration.

## Cookbook Sources
- `cookbook/guidelines/kotlin/`
- Cross-cutting: accessibility, UI, platform compliance

## Structured Questions

1. What's your font scaling support? If a user sets their device to largest font, does your app remain usable?

2. Are you using Jetpack Compose, XML layouts, or a mix? What's driving that choice?

3. What's your architecture — MVVM, MVI, or something else? How do you manage state?

4. Material Design compliance — are you using Material 3 components? Where do you deviate from Material guidelines?

5. How do you handle Android fragmentation — different screen sizes, API levels, manufacturer skins?

6. What's your minimum SDK version? How do you handle features not available on older versions?

7. Describe your navigation — Jetpack Navigation, custom, or something else? Deep linking support?

8. How do you manage background work — WorkManager, foreground services, or something else? Battery optimization considerations?

9. What permissions does your app request? How do you handle permission denial gracefully?

10. How do you test on different devices? Physical devices, emulators, Firebase Test Lab?

11. What's your Play Store submission process? Staged rollouts? How do you handle reviews?

12. How do you handle the back button and system navigation gestures consistently?

## Exploratory Prompts

1. What if your app had to work on a $50 phone with 2GB RAM? What would you cut first?

2. How does Android's activity lifecycle affect your architecture? Where have you been bitten by lifecycle issues?

3. If Google deprecated a Jetpack library you depend on, how prepared are you?

4. What's the difference between "works on Pixel" and "works on Android"? How do you close that gap?
