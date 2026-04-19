---

id: 0935bc69-88a9-483e-a3c9-38447d880f45
title: "State Design"
domain: agentic-cookbook://guidelines/implementing/ui/state-design
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Every view that loads data or can be empty must handle all four states explicitly. Never"
platforms: 
  - typescript
  - web
tags: 
  - state-design
  - ui
depends-on: []
related: 
  - agentic-cookbook://guidelines/ui/always-show-progress
references: 
  - https://developer.apple.com/design/human-interface-guidelines/empty-states
  - https://material.io/design/communication/empty-states.html
  - https://www.nngroup.com/articles/empty-state-interface-design/
  - https://www.nngroup.com/articles/error-message-guidelines/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
  - data-modeling
---

# State Design

Every view that loads data or can be empty MUST handle all four states explicitly. A blank
screen with no explanation MUST NOT be shown.

**The four states:**

1. **Loading** — show progress (see agentic-cookbook://guidelines/ui/always-show-progress). Use skeleton screens for content-heavy
   views, spinners for actions. Never block the entire screen for a partial load.
2. **Empty** — explain what belongs here, why it's empty, and provide a single clear action to
   populate it. Use an icon or illustration, a brief message, and a CTA button.
3. **Error** — identify the problem, explain why if possible, and offer a recovery action (retry,
   go back, contact support). Raw error codes or stack traces MUST NOT be shown. Don't blame the user.
4. **Loaded** — the normal content state.

Design empty and error states with the same care as the loaded state — they are often the
user's first impression.

References:
- [Apple HIG: Empty States](https://developer.apple.com/design/human-interface-guidelines/empty-states)
- [NNGroup: Empty State Design](https://www.nngroup.com/articles/empty-state-interface-design/)
- [NNGroup: Error Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/)
- [Material Design: Empty States (M2 reference)](https://material.io/design/communication/empty-states.html)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
