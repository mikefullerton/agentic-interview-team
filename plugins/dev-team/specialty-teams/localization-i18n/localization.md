---
name: localization
description: All user-facing strings externalized into platform-standard resource files — `.xcstrings`/`.strings` (Swift), `strings.x...
artifact: guidelines/internationalization/localization.md
version: 1.0.0
---

## Worker Focus
All user-facing strings externalized into platform-standard resource files — `.xcstrings`/`.strings` (Swift), `strings.xml` (Kotlin), message catalogs via `react-intl`/`i18next` (TypeScript), `.resw` with `x:Uid` (Windows); no hardcoded strings; locale-aware APIs for dates, numbers, currencies; plural rules for all supported locales

## Verify
No literal user-facing strings in source code; platform localization API used throughout; date/number formatting uses locale-aware APIs not hardcoded format strings; plural forms cover non-English rules where applicable
