---
name: feedback-patterns
description: Implement toast/snackbar (auto-dismiss 3-5s), inline alerts/banners, and modal dialogs; connect feedback weight to actio...
artifact: guidelines/ui/feedback-patterns.md
version: 1.0.0
---

## Worker Focus
Implement toast/snackbar (auto-dismiss 3-5s), inline alerts/banners, and modal dialogs; connect feedback weight to action weight; no `alert()` or dialogs for success; default focus on Cancel in destructive dialogs

## Verify
Toast auto-dismisses after 3-5s; success never triggers `window.alert()` or `<dialog>`; destructive dialogs use explicit labels (not "OK"); focus set to Cancel/safe button on dialog open
