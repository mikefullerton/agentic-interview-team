---

id: 3d970d6a-2d71-48f3-9f84-69c1d823d6e8
title: "Accessibility from day one"
domain: agentic-cookbook://guidelines/implementing/accessibility/accessibility
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "All components MUST integrate with platform accessibility APIs from initial implementation:"
platforms: 
  - csharp
  - kotlin
  - swift
  - typescript
  - web
  - windows
tags: 
  - accessibility
depends-on: []
related: []
references: 
  - https://accessibilityinsights.io/
  - https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-uiautomationoverview
  - https://www.w3.org/TR/WCAG21/
  - https://www.w3.org/WAI/ARIA/apg/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - accessibility
  - ui-implementation
  - pre-pr
---

# Accessibility from day one

All components MUST integrate with platform accessibility APIs from initial implementation:

1. Semantic roles and labels on all interactive elements
2. VoiceOver (Apple) / TalkBack (Android) / screen reader (Web) full support
3. Keyboard and switch control navigation
4. Dynamic Type / font scaling — layouts MUST NOT break at larger text sizes
5. WCAG AA minimum contrast (4.5:1 for text, 3:1 for large text)
6. Meaningful focus order following visual layout

Platform-specific tooling:
- **Windows**: UI Automation patterns, Narrator testing, [Accessibility Insights](https://accessibilityinsights.io/), minimum 40x40 epx recommended touch targets

# Respect accessibility display options

Components MUST respond to platform accessibility and display settings including reduced motion, high contrast, color inversion, bold text, and grayscale. See platform-specific files for the full list of settings and environment keys.

---

# Accessibility

All components MUST integrate with platform accessibility APIs from initial implementation. Requirements:

1. Semantic roles and labels on all interactive elements
2. Screen reader full support (VoiceOver, TalkBack, Narrator, ARIA)
3. Keyboard and switch control navigation
4. Dynamic Type / font scaling — layouts MUST NOT break at larger text sizes
5. WCAG AA minimum contrast (4.5:1 for text, 3:1 for large text)
6. Meaningful focus order following visual layout
7. Components MUST respond to platform accessibility and display settings including reduced motion, high contrast, color inversion, bold text, and grayscale

## Swift

Components MUST respond to these SwiftUI environment values:

| Setting | Environment Key | Action |
|---------|----------------|--------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Reduce Motion | `\.accessibilityReduceMotion` | Replace animations with crossfades or instant transitions |
| Reduce Transparency | `\.accessibilityReduceTransparency` | Use opaque backgrounds instead of blurs/vibrancy |
| Differentiate Without Color | `\.accessibilityDifferentiateWithoutColor` | Add icons/shapes/patterns alongside color indicators |
| Increase Contrast | `\.colorSchemeContrast` | Use higher-contrast color pairs |
| Invert Colors | `isInvertColorsEnabled` | Mark images/video with `accessibilityIgnoresInvertColors` |
| Cross-Fade Transitions | `prefersCrossFadeTransitions` | Use cross-fade instead of slide/zoom transitions |

## Kotlin

Components MUST respond to these Android accessibility settings:

| Setting | API | Action |
|---------|-----|--------|
| Remove Animations | `animator_duration_scale == 0` | Disable all custom animations |
| Font Scale | `Configuration.fontScale` | Ensure layouts handle 2x font size |
| High Contrast Text | System setting | Ensure text meets WCAG AA contrast ratios |
| Color Inversion | `ACCESSIBILITY_DISPLAY_INVERSION_ENABLED` | Mark media with `importantForAccessibility` |
| TalkBack | `AccessibilityManager` | All elements have `contentDescription` and proper roles |
| Switch Access | `AccessibilityManager` | All interactive elements are focusable and reachable |
| Dark Theme | `Configuration.uiMode` | Full dark theme support |
| Display Size | `displayMetrics.density` | Layouts must not break at larger display sizes |

## TypeScript

### Standards

1. [WCAG 2.1](https://www.w3.org/TR/WCAG21/) — minimum AA conformance for all components.
2. [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/) — correct ARIA roles, states, and properties.

### CSS Media Queries

Components MUST respond to these user preferences:

| Setting | Media Query | Action |
|---------|-------------|--------|
| Reduced Motion | `prefers-reduced-motion: reduce` | Disable/simplify CSS animations and JS transitions |
| High Contrast | `prefers-contrast: more` | Increase border widths, use higher-contrast colors |
| Forced Colors | `forced-colors: active` | Respect system color palette (Windows High Contrast) |
| Dark Mode | `prefers-color-scheme: dark` | Full dark theme support |
| Reduced Transparency | `prefers-reduced-transparency: reduce` | Use opaque backgrounds |
| Reduced Data | `prefers-reduced-data: reduce` | Lazy-load images, reduce asset sizes |

Screen reader support: use ARIA roles, `aria-live` for dynamic content, proper landmark regions.

## Windows

WinUI 3 controls expose [UI Automation](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-uiautomationoverview) patterns automatically. Set `AutomationProperties.Name` on interactive elements that lack visible text labels.

- Use `AutomationProperties.LabeledBy` for form fields
- Use `AutomationProperties.LiveSetting` for dynamic content regions
- High contrast support is automatic when using `ThemeResource` — never hard-code colors
- Test with [Accessibility Insights for Windows](https://accessibilityinsights.io/)
- Keyboard navigation: all interactive elements must be reachable via Tab, actionable via Enter/Space

Components MUST respond to these Windows accessibility settings:

| Setting | API / Detection | Action |
|---------|----------------|--------|
| High Contrast | `AccessibilitySettings.HighContrast` | Automatic via ThemeResource — verify custom visuals adapt |
| Animations Disabled | `UISettings.AnimationsEnabled` | Disable all custom animations and transitions |
| Text Scaling | `UISettings.TextScaleFactor` | Layouts must not break up to 225% text scale |
| Color Filters | System setting | Ensure UI is usable with color vision deficiency filters |
| Narrator | UI Automation tree | All elements have Name, Role, and appropriate patterns |
| Keyboard Navigation | Focus management | All interactive elements reachable via Tab, actionable via Enter/Space |
| Dark Theme | `Application.RequestedTheme` | Full dark theme support via ThemeResource |
| Caret Browsing | System setting | Non-interactive text should be navigable |

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
