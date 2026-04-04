---
name: state-design
description: Implement all four states in component templates — loading (skeleton/spinner), empty (illustration + message + CTA butto...
artifact: guidelines/ui/state-design.md
version: 1.0.0
---

## Worker Focus
Implement all four states in component templates — loading (skeleton/spinner), empty (illustration + message + CTA button), error (message + retry/back action), loaded; never render blank DOM with no explanation

## Verify
All four states render for every data-loading component; empty state has visible CTA; error state has retry or navigation action; no raw error codes or stack traces in DOM
