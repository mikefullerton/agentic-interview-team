---
name: deep-linking
description: Protocol activation via `<uap:Protocol>` declaration in `Package.appxmanifest`; handle activation through `AppInstance.G...
artifact: guidelines/platform/deep-linking.md
version: 1.0.0
---

## Worker Focus
Protocol activation via `<uap:Protocol>` declaration in `Package.appxmanifest`; handle activation through `AppInstance.GetActivatedEventArgs()` in `App.OnLaunched`; use `AppInstance.FindOrRegisterForKey()` for single-instancing; parse URI to determine target page/state and navigate accordingly; every significant view must be reachable via protocol activation

## Verify
`<uap:Protocol>` declared in manifest; `AppInstance.GetActivatedEventArgs()` handled in `OnLaunched`; URI parsed to navigate to correct page; single-instancing implemented; deep linking section in spec defines URI patterns
