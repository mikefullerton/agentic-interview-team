# Localization & I18n Specialist

## Domain Coverage
String externalization, RTL support, locale-aware formatting, text expansion, Unicode, layout flexibility, plural rules, font fallback.

## Cookbook Sources
- `cookbook/guidelines/internationalization/`
- `cookbook/compliance/internationalization.md`

## Structured Questions

1. How many languages do you currently support? Planning to support? Who decides which languages?

2. Walk me through how a user-facing string gets added. Is there a process, or can developers add strings directly in code?

3. How do you manage translations? Vendor, community, or in-house? How often updated?

4. Describe your experience with right-to-left languages. Tested with Hebrew or Arabic? What broke?

5. How do you handle text expansion? "Save" → "Speichern" — does your UI still work?

6. What's your approach to plural forms? Languages where pluralization differs from English (Polish, Russian)?

7. How do you localize dates, times, and numbers? Hardcoded format strings or locale-aware APIs?

8. Custom fonts — do they work in all supported languages? Font fallback for uncovered character sets?

9. Emoji and special characters — hit any issues with rendering or filtering?

10. How do you test localization? Every language or representative sample? On actual devices in those regions?

11. Dynamic type / font scaling story? If user increases text size, does your app still work?

12. How do layouts adapt for different text lengths? Constraint-based, or does text get truncated?

## Exploratory Prompts

1. What if you had to support a language you don't speak? How would you verify the translation is culturally appropriate, not just grammatically correct?

2. Why is RTL more than just mirroring text? What assumptions about directionality are baked into your UI?

3. If text expansion broke half your layouts, how would you discover that before shipping?

4. What's the relationship between localization and accessibility? Separate concerns or intertwined?
