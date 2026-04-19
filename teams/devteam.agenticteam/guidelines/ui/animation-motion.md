---

id: 9f13dbec-cecb-482b-824b-f7d3e341878a
title: "Animation & Motion"
domain: agentic-cookbook://guidelines/implementing/ui/animation-motion
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Motion should be purposeful — guide attention, show spatial relationships, and provide"
platforms: 
  - windows
tags: 
  - animation-motion
  - ui
depends-on: []
related: 
  - agentic-cookbook://guidelines/accessibility/accessibility
references: 
  - https://developer.apple.com/design/human-interface-guidelines/motion
  - https://learn.microsoft.com/en-us/windows/apps/design/motion/timing-and-easing
  - https://m3.material.io/styles/motion/overview
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
  - accessibility
---

# Animation & Motion

Motion should be purposeful — guide attention, show spatial relationships, and provide
feedback. Never animate for decoration.

**Duration defaults** (when no platform value exists):

| Interaction | Duration |
|------------|----------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Micro-feedback (ripple, highlight) | 50-100ms |
| State change (hover, toggle, press) | 100-200ms |
| Component enter/exit | 200-350ms |
| Page/navigation transition | 300-500ms |
| Complex choreography (rare) | 500-1000ms |

- Under 100ms feels instant. Over 500ms feels sluggish.
- Platform-native spring/easing curves SHOULD be preferred over linear or custom beziers
- **Reduced-motion preferences MUST be respected** — see agentic-cookbook://guidelines/accessibility/accessibility and each platform
  file's accessibility settings table. When reduced motion is enabled, replace animations
  with instant state changes or simple cross-fades.
- Motion SHOULD NOT cover large distances, loop continuously, or flash

References:
- [Apple HIG: Motion](https://developer.apple.com/design/human-interface-guidelines/motion)
- [Material Design: Motion](https://m3.material.io/styles/motion/overview)
- [Fluent Design: Timing and Easing](https://learn.microsoft.com/en-us/windows/apps/design/motion/timing-and-easing)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
