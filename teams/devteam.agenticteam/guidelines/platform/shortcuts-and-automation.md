---

id: 991e72d0-477b-4fd5-bdfa-08680efc0cf9
title: "Scriptable and automatable"
domain: agentic-cookbook://guidelines/implementing/platform-integration/shortcuts-and-automation
type: guideline
version: 1.1.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Components and flows SHOULD be scriptable where the platform supports it:"
platforms: 
  - csharp
  - ios
  - kotlin
  - macos
  - swift
  - web
  - windows
tags: 
  - shortcuts-and-automation
  - platform
depends-on:
  - agentic-cookbook://principles/support-automation
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - platform-integration
  - configuration
---

# Scriptable and automatable

Components and flows SHOULD be scriptable where the platform supports it:

- **Apple (macOS)**: `AppIntents` for Shortcuts, AppleScript via `NSScriptCommand`
- **Apple (iOS)**: `AppIntents` for Shortcuts and Siri integration
- **Android**: `AppActions` for Google Assistant, `Intent`-based automation
- **Web**: API endpoints or query parameter-driven actions
- **Windows**: Protocol activation, command-line activation, `AppInstance` APIs. WinUI 3 has limited scripting support compared to other platforms.

---

# Shortcuts and Automation

Components and flows SHOULD be scriptable where the platform supports it. Automation enables power users to integrate app functionality into workflows, voice assistants, and third-party tools.

## Swift

Use the `AppIntents` framework for Shortcuts and Siri integration. On macOS, support AppleScript via `NSScriptCommand` where appropriate.

## Kotlin

Use `AppActions` for Google Assistant integration. Support `Intent`-based automation.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.1.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.1.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
| 1.1.0 | 2026-04-02 | Mike Fullerton | Moved from ui/ to platform/ — system integration, not UI design |
