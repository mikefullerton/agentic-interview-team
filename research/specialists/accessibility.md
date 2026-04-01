# Accessibility Specialist

## Domain Coverage
Screen reader support, keyboard navigation, dynamic type/font scaling, color contrast, reduced motion, touch/click targets, platform accessibility APIs, focus management, semantic markup, color independence.

## Cookbook Sources
- `cookbook/guidelines/accessibility/`
- `cookbook/compliance/accessibility.md`

## Structured Questions

1. How are you planning to test screen reader compatibility? VoiceOver (iOS), TalkBack (Android), ARIA (web), Narrator (Windows)? Plans for `aria-live` regions for dynamic content?

2. Will all features be accessible via keyboard only? What's your focus order strategy? Visible focus indicators?

3. How will your UI respond when users increase system font size? Responsive font sizing or fixed pixels? At what size does your layout break?

4. What color palette are you using? Tested contrast ratios against WCAG AA (4.5:1)? Plan for high-contrast mode?

5. Does your app use animations — transitions, parallax, autoplaying carousels? What happens when "reduce motion" is enabled?

6. What's the minimum size of interactive elements? At least 44x44pt or 48x48dp? How do you handle elements that must be smaller?

7. Are you using native accessibility APIs from day one or retrofitting later?

8. If your app has modal dialogs, how will you trap focus inside them? After closing a modal, where does focus go?

9. Semantic HTML elements (button, nav, main, form) or generic divs with ARIA? Do you understand the difference between `role` and `aria-label`?

10. How will you handle images — alt text on all? For icon-only buttons, `aria-label` or visible text?

11. Does your design rely on color alone to convey status, errors, or required fields? Icons, borders, text labels alongside colors?

12. What's your accessibility testing strategy — automated tools (axe, Lighthouse), manual screen reader testing, or user testing with people who have disabilities?

## Exploratory Prompts

1. What if a user couldn't use a mouse or touch screen? Could they use your app with just keyboard or voice control? Where would it break?

2. Design a key feature that currently relies on color to work for someone with color blindness. How would you change it?

3. If your app uses audio cues or video content, how would a deaf user experience it?

4. As you add features, how will you maintain accessibility? What process prevents new features from breaking existing accessibility?

5. What's the relationship between accessibility and good design? Where do they reinforce each other?
