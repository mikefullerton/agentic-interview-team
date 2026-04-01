# UI/UX & Design Specialist

## Domain Coverage
Layout, color, typography, animation, forms, visual hierarchy, feedback patterns, state design (loading/empty/error/loaded), deep linking, platform design languages, progress indication.

## Cookbook Sources
- `cookbook/guidelines/ui/` (17+ guidelines)
- `cookbook/compliance/platform-compliance.md`

## Structured Questions

1. Walk me through what happens when a user opens your app and no data has loaded yet. What does the screen show for the first 2-5 seconds? Skeleton, spinner, or blank?

2. Your app shows a list that can be empty — how many states have you designed? What does the empty state look like? What's the next-action button?

3. Tell me about the most destructive action in your app. What happens on accidental delete? Confirmation dialog — what does it say? What's the default button?

4. When the user submits a form with validation errors, where do they appear? Top? Inline under each field? Color-coded, or with icons and text?

5. How many fields in your main form are actually required? Walk me through why each one is there. Pre-filling anything?

6. Your app saves data or makes a network request — what feedback does the user get while waiting? If it takes 10 seconds, does the feedback change?

7. Can a user share a link to a specific feature or piece of content? Deep links — will they land in the right place with context?

8. When something goes wrong (network error, server error, timeout), what does the user see? Raw error code or human-readable message with recovery action?

9. When should form validation errors show? As they type, when they leave the field, or only on submit?

10. Are you using native controls and design languages for each platform, or a custom consistent design across all?

11. Do power-user flows support automation — Siri shortcuts, voice assistants, keyboard shortcuts, APIs?

12. Your primary call-to-action button — where does it live? Is it ever disabled? What does the user see when it is?

13. You're building for light and dark mode — how does your color palette and contrast change between them?

14. On mobile with a small screen, how many form fields are visible at once? Scroll or multi-step? How do you show progress?

15. What's your approach to spacing and visual hierarchy? How do you guide the user's eye to what matters most?

## Exploratory Prompts

1. What if your most common user action had zero feedback? What would the ripple effects be?

2. Imagine your app is used with poor connectivity. How would that change your approach to feedback, validation, and error messaging?

3. If you removed all "Are you sure?" dialogs, what would actually break? Which destructive actions are truly worth the confirmation friction?

4. What if a user is interrupted mid-task (phone call, app switch)? When they come back, what state are they in?

5. How do platform design languages (HIG, Material, Fluent) influence your decisions? Where do you follow conventions, where do you break them?
