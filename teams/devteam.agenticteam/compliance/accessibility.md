---
id: 27846525-7E10-49F1-B1ED-06840FAF6120
title: "Accessibility"
domain: agentic-cookbook://compliance/accessibility
type: compliance
version: 1.0.0
status: draft
language: en
created: 2026-03-28
modified: 2026-03-28
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Compliance checks for accessibility, assistive technology support, and inclusive design."
platforms: []
tags: [compliance, accessibility]
depends-on: []
related:
  - agentic-cookbook://compliance/platform-compliance
  - agentic-cookbook://compliance/internationalization
  - agentic-cookbook://compliance/performance
references: []
---

# Accessibility

Compliance checks that ensure user interfaces are perceivable, operable, understandable, and robust for all users, including those who rely on assistive technologies. These checks align with WCAG guidelines and platform-specific accessibility standards.

## Applicability

All recipes with a user interface. Guidelines covering UI patterns, interaction design, or visual presentation.

## Checks

### screen-reader-support

All interactive elements MUST be accessible to screen readers with meaningful labels.

**Applies when:** a component renders interactive UI elements (buttons, links, form controls, custom widgets).

**Guidelines:**
- [Accessibility](agentic-cookbook://guidelines/accessibility/accessibility)

---

### keyboard-navigable

All functionality MUST be operable via keyboard or equivalent non-pointer input.

**Applies when:** a component provides interactive functionality.

**Guidelines:**
- [Accessibility](agentic-cookbook://guidelines/accessibility/accessibility)

---

### dynamic-type-support

Text MUST scale with system font size settings on all platforms.

**Applies when:** a component displays text content.

**Guidelines:**
- [Dynamic Type](agentic-cookbook://guidelines/accessibility/dynamic-type)
- [Font Scaling](agentic-cookbook://guidelines/accessibility/font-scaling)

---

### contrast-ratio

Text and interactive elements MUST meet WCAG AA contrast ratio (4.5:1 for normal text, 3:1 for large text).

**Applies when:** a component renders text or interactive elements with foreground/background color combinations.

**Guidelines:**
- [Accessibility](agentic-cookbook://guidelines/accessibility/accessibility)

---

### touch-target-size

Touch and click targets MUST be at least 44x44pt (Apple) or 48x48dp (Android).

**Applies when:** a component renders tappable or clickable elements.

**Guidelines:**
- [Touch and Click Targets](agentic-cookbook://guidelines/ui/touch-click-targets)

---

### reduced-motion

Animations MUST respect the system reduced-motion preference.

**Applies when:** a component uses animation or motion effects.

**Guidelines:**
- [Accessibility](agentic-cookbook://guidelines/accessibility/accessibility)
- [Animation and Motion](agentic-cookbook://guidelines/ui/animation-motion)

---

### focus-management

Focus MUST be managed logically; modal content MUST trap focus appropriately.

**Applies when:** a component manages focus order, presents modal dialogs, or uses overlays.

**Guidelines:**
- [Accessibility](agentic-cookbook://guidelines/accessibility/accessibility)

---

### semantic-markup

Web components MUST use correct ARIA roles, states, and properties.

**Applies when:** a component renders web-based UI using HTML/ARIA.

**Guidelines:**
- [Accessibility](agentic-cookbook://guidelines/accessibility/accessibility)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-28 | Mike Fullerton | Initial creation |
