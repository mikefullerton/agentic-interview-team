---
name: performance-compliance
description: 8 compliance checks — main-thread-freedom, animation-frame-rate (60fps/16ms), lazy-loading, resource-efficiency, startup...
artifact: compliance/performance.md
version: 1.0.0
---

## Worker Focus
8 compliance checks — main-thread-freedom, animation-frame-rate (60fps/16ms), lazy-loading, resource-efficiency, startup-impact, image-optimization, caching-strategy, progress-indication (operations >200ms)

## Verify
Each compliance check has a status (passed/failed/partial/n-a) with evidence; no blocking calls on main/UI thread; progress shown for operations exceeding 200ms; large collections use lazy loading or pagination
