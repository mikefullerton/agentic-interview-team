---

id: 57cbdb9d-4cf7-4a39-bdd8-99d28be983ca
title: "Localizability"
domain: agentic-cookbook://guidelines/implementing/internationalization/localization
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "All user-facing strings MUST be localizable — no hardcoded strings:"
platforms: 
  - csharp
  - kotlin
  - swift
  - typescript
  - web
  - windows
tags: 
  - internationalization
  - localization
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - internationalization
  - ui-implementation
---

# Localizability

All user-facing strings MUST be localizable — no hardcoded strings:

- **Apple**: `String(localized:)` or `NSLocalizedString`. Store in `.xcstrings` or `.strings`.
- **Android**: `strings.xml` resources. Reference via `R.string.*` or `stringResource()`.
- **Web**: i18n library (`react-intl`, `i18next`). Extract to message catalogs.
- **Windows**: `.resw` resource files with `x:Uid` in XAML. `ResourceLoader` from MRT Core for code-behind access.

---

# Localization

All user-facing strings MUST be localizable. No hardcoded strings. Store strings in platform-standard resource files and reference them through the platform's localization API.

## Swift

Use `String(localized:)` (Swift 5.7+) or `NSLocalizedString`. Store strings in `.xcstrings` (Xcode 15+) or `.strings` files. No hardcoded user-facing strings.

## Kotlin

Use `strings.xml` resource files. Reference via `R.string.*` in code or `stringResource()` in Compose. No hardcoded user-facing strings.

## TypeScript

Use an i18n library (`react-intl`, `i18next`, `FormatJS`). Extract all user-facing strings into message catalogs. No hardcoded strings.

## Windows

Use MRT Core with `.resw` resource files. The `x:Uid` directive in XAML binds control properties to resource keys.

- `x:Uid="SaveButton"` maps to `SaveButton.Content`, `SaveButton.AutomationProperties.Name`, etc. in the `.resw` file
- Folder structure: `Strings/<language-tag>/Resources.resw` (e.g., `Strings/en-US/Resources.resw`)
- Code-behind access via `Microsoft.Windows.ApplicationModel.Resources.ResourceLoader`
- No hardcoded user-facing strings

```xml
<!-- XAML: localized via x:Uid -->
<Button x:Uid="SaveButton" />
```

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
