---

id: ca9874ea-07ed-4585-8692-33a29bc6411a
title: "Feedback Patterns"
domain: agentic-cookbook://guidelines/implementing/ui/feedback-patterns
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Every user action should have visible feedback. The weight of the feedback should match"
platforms: []
tags: 
  - feedback-patterns
  - ui
depends-on: []
related: []
references: 
  - https://developer.apple.com/design/human-interface-guidelines/alerts
  - https://m3.material.io/components/snackbar/overview
  - https://www.nngroup.com/articles/confirmation-dialog/
  - https://www.nngroup.com/articles/ten-usability-heuristics/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
  - error-handling
---

# Feedback Patterns

Every user action should have visible feedback. The weight of the feedback should match
the weight of the action.

- **Inline feedback** — field-level validation, character counts, progress within a component.
  Lowest weight, least disruptive.
- **Toast / Snackbar** — non-critical confirmations ("Saved", "Copied to clipboard"). Auto-dismiss
  after 3-5 seconds. No user action required. Toasts MUST NOT be used for errors.
- **Banner / Inline alert** — persistent messages that need attention but don't block work
  (connectivity warning, degraded mode). Dismissible.
- **Dialog / Alert** — destructive or irreversible actions requiring explicit confirmation
  ("Delete 12 items? This cannot be undone."). Use sparingly — dialog fatigue leads to
  click-through without reading.
- Dialogs MUST NOT be used for success messages — a toast or inline confirmation is sufficient.
- **Destructive actions** MUST require explicit confirmation with a clearly labeled action
  ("Delete", not "OK"). Default focus should be on the safe option (Cancel).

References:
- [Apple HIG: Alerts](https://developer.apple.com/design/human-interface-guidelines/alerts)
- [Material Design: Snackbar](https://m3.material.io/components/snackbar/overview)
- [NNGroup: Confirmation Dialogs](https://www.nngroup.com/articles/confirmation-dialog/)
- [NNGroup: Ten Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) (Heuristic #1: Visibility of system status)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
