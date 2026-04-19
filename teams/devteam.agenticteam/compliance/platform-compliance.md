---
id: 9D54950C-FED8-40DA-8F68-B01508884D6C
title: "Platform Compliance"
domain: agentic-cookbook://compliance/platform-compliance
type: compliance
version: 1.0.0
status: draft
language: en
created: 2026-03-28
modified: 2026-03-28
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Compliance checks for platform-specific design, conventions, and store policies."
platforms: []
tags: [compliance, platform]
depends-on: []
related:
  - agentic-cookbook://compliance/accessibility
  - agentic-cookbook://compliance/performance
  - agentic-cookbook://compliance/user-safety
references: []
---

# Platform Compliance

Compliance checks that ensure components respect platform-specific design languages, conventions, and distribution policies. These checks promote native-feeling experiences and smooth app store approval across Apple, Android, Windows, and web platforms.

## Applicability

All recipes targeting a specific platform. Guidelines covering platform-specific patterns or UI design.

## Checks

### platform-design-language

UI MUST follow the platform's native design language (HIG, Material, Fluent).

**Applies when:** a component renders user interface on a specific platform.

**Guidelines:**
- [Platform Design Languages](agentic-cookbook://guidelines/ui/platform-design-languages)

---

### native-controls-preference

Standard UI patterns SHOULD use native platform controls before custom implementations.

**Applies when:** a component implements common UI patterns (lists, navigation, dialogs, pickers).

**Guidelines:**
- [Native Controls](agentic-cookbook://principles/native-controls)

---

### platform-touch-targets

Interactive elements MUST meet platform-specific minimum touch target sizes.

**Applies when:** a component renders tappable or clickable elements on mobile or touch-enabled platforms.

**Guidelines:**
- [Touch and Click Targets](agentic-cookbook://guidelines/ui/touch-click-targets)

---

### deep-linking-support

Features with addressable content MUST support platform deep linking conventions.

**Applies when:** a component presents content that should be navigable via external links.

**Guidelines:**
- [Deep Linking](agentic-cookbook://guidelines/platform/deep-linking)

---

### platform-permissions

Features MUST request only the minimum platform permissions required.

**Applies when:** a recipe requires system capabilities (camera, location, contacts, etc.).

---

### app-store-guidelines

iOS/macOS recipes MUST comply with Apple App Store Review Guidelines.

**Applies when:** a recipe targets Apple platforms.

---

### play-store-policies

Android recipes MUST comply with Google Play Developer Program Policies.

**Applies when:** a recipe targets Android/Google Play.

---

### platform-theming

Components MUST support platform theming (dark mode, high contrast, accent colors).

**Applies when:** a component renders UI that should adapt to system appearance settings.

**Guidelines:**
- [Theming](agentic-cookbook://guidelines/ui/theming)
- [Color](agentic-cookbook://guidelines/ui/color)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-28 | Mike Fullerton | Initial creation |
