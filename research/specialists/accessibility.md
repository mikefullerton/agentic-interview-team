# Accessibility Specialist

## Role
Platform accessibility APIs, screen readers, keyboard navigation, font scaling, contrast, reduced motion, touch targets, focus management, semantic markup.

## Persona
(coming)

## Cookbook Sources
- `guidelines/accessibility/accessibility.md`
- `compliance/accessibility.md`

## Specialty Teams

### accessibility
- **Artifact**: `guidelines/accessibility/accessibility.md`
- **Worker focus**: Semantic roles and labels on all interactive elements; full screen reader support (VoiceOver, TalkBack, Narrator, ARIA); keyboard and switch control navigation; Dynamic Type/font scaling without layout breakage; WCAG AA contrast (4.5:1 text, 3:1 large text); meaningful focus order; platform accessibility display settings (reduced motion, high contrast, color inversion, bold text, grayscale)
- **Verify**: Every interactive element has a semantic role and accessible label; layouts tested at 2x font scale without clipping or overflow; contrast ratios verified at 4.5:1 for normal text; `prefers-reduced-motion` / `accessibilityReduceMotion` honored; platform-specific APIs used (SwiftUI environment keys, Android `AccessibilityManager`, ARIA roles + `aria-live`, Windows `AutomationProperties`)

### accessibility-compliance
- **Artifact**: `compliance/accessibility.md`
- **Worker focus**: 8 compliance checks — screen-reader-support, keyboard-navigable, dynamic-type-support, contrast-ratio, touch-target-size, reduced-motion, focus-management, semantic-markup
- **Verify**: Each compliance check has a status (passed/failed/partial/n-a) with evidence; touch targets verified at ≥44x44pt (Apple) or ≥48x48dp (Android); modal dialogs trap and restore focus; web components use correct ARIA roles, states, and properties

## Exploratory Prompts

1. What if a user couldn't use a mouse or touch screen? Could they use your app with just keyboard or voice control? Where would it break?

2. Design a key feature that currently relies on color to work for someone with color blindness. How would you change it?

3. If your app uses audio cues or video content, how would a deaf user experience it?

4. As you add features, how will you maintain accessibility? What process prevents new features from breaking existing accessibility?

5. What's the relationship between accessibility and good design? Where do they reinforce each other?
