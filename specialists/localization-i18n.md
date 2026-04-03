# Localization & I18n Specialist

## Role
String externalization, RTL support, locale-aware formatting, text expansion, Unicode, layout flexibility, plural rules, font fallback.

## Persona
(coming)

## Cookbook Sources
- `guidelines/internationalization/localization.md`
- `guidelines/internationalization/rtl-support.md`
- `compliance/internationalization.md`

## Specialty Teams

### localization
- **Artifact**: `guidelines/internationalization/localization.md`
- **Worker focus**: All user-facing strings externalized into platform-standard resource files — `.xcstrings`/`.strings` (Swift), `strings.xml` (Kotlin), message catalogs via `react-intl`/`i18next` (TypeScript), `.resw` with `x:Uid` (Windows); no hardcoded strings; locale-aware APIs for dates, numbers, currencies; plural rules for all supported locales
- **Verify**: No literal user-facing strings in source code; platform localization API used throughout; date/number formatting uses locale-aware APIs not hardcoded format strings; plural forms cover non-English rules where applicable

### rtl-support
- **Artifact**: `guidelines/internationalization/rtl-support.md`
- **Worker focus**: Leading/trailing (not left/right) for all alignment and padding; directional icons mirrored; non-directional icons not mirrored; `android:supportsRtl="true"` on Android, CSS logical properties on web, `FlowDirection` on Windows; RTL locale tested
- **Verify**: No `left`/`right` layout constraints or CSS properties — only leading/trailing/logical equivalents; `supportsRtl` manifest flag set on Android; directional icons have RTL variants; RTL locale tested in preview or emulator

### internationalization-compliance
- **Artifact**: `compliance/internationalization.md`
- **Worker focus**: 7 compliance checks — string-externalization, rtl-layout-support, locale-aware-formatting, plural-forms, text-expansion-tolerance (up to 200%), unicode-support (full Unicode including emoji), no-hardcoded-strings
- **Verify**: Each compliance check has a status (passed/failed/partial/n-a) with evidence; text expansion tested at ≥150% string length; Unicode handling confirmed for emoji and multi-byte characters

## Exploratory Prompts

1. What if you had to support a language you don't speak? How would you verify the translation is culturally appropriate, not just grammatically correct?

2. Why is RTL more than just mirroring text? What assumptions about directionality are baked into your UI?

3. If text expansion broke half your layouts, how would you discover that before shipping?

4. What's the relationship between localization and accessibility? Separate concerns or intertwined?
