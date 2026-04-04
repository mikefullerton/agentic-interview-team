---
name: state-design
description: All four states explicit — loading (skeleton for content-heavy, spinner for actions), empty (icon + message + CTA), erro...
artifact: guidelines/ui/state-design.md
version: 1.0.0
---

## Worker Focus
All four states explicit — loading (skeleton for content-heavy, spinner for actions), empty (icon + message + CTA), error (problem + reason + recovery action, no raw codes), loaded; empty and error designed with same care as loaded

## Verify
All four states present for every data-loading view; no blank screen on empty; no raw error codes or stack traces shown to user; empty state has CTA; error state has recovery action
