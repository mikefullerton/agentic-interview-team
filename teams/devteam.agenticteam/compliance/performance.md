---
id: 4325D8FF-ECB5-460B-836E-4F55309F2DC0
title: "Performance Compliance"
domain: agentic-cookbook://compliance/performance
type: compliance
version: 1.0.0
status: draft
language: en
created: 2026-03-28
modified: 2026-03-28
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Compliance checks for main-thread responsiveness, frame rates, lazy loading, and resource efficiency."
platforms: []
tags: [compliance, performance]
depends-on: []
related:
  - agentic-cookbook://compliance/reliability
  - agentic-cookbook://compliance/accessibility
  - agentic-cookbook://compliance/access-patterns
references: []
---

# Performance Compliance

Performance compliance ensures that implementations remain responsive, efficient, and resource-conscious across all platforms. These checks cover main-thread discipline, animation smoothness, data loading strategies, memory and CPU usage, startup impact, image handling, caching, and user-perceived latency.

## Applicability

This category applies to any recipe or guideline that renders UI, loads data, displays images, manages long-lived components, or performs work during app startup. If a recipe affects what the user sees or how quickly they see it, these checks apply.

## Checks

### main-thread-freedom

UI updates and rendering MUST NOT block the main thread.

**Applies when:** recipe performs computation, I/O, or network calls alongside UI rendering.

**Guidelines:**
- [Concurrency](agentic-cookbook://guidelines/concurrency/concurrency)

---

### animation-frame-rate

Animations MUST target 60fps; frames MUST NOT exceed 16ms.

**Applies when:** recipe includes animations, transitions, or motion effects.

**Guidelines:**
- [Animation and Motion](agentic-cookbook://guidelines/ui/animation-motion)

---

### lazy-loading

Large data sets and heavy resources MUST use lazy loading or pagination.

**Applies when:** recipe displays lists, grids, or collections of unbounded size.

**Guidelines:**
- [Data Display](agentic-cookbook://guidelines/ui/data-display)
- [Pagination](agentic-cookbook://guidelines/networking/pagination)

---

### resource-efficiency

Components MUST minimize memory allocations and CPU usage during idle states.

**Applies when:** recipe defines a long-lived component.

---

### startup-impact

Components MUST NOT add measurable delay to app startup.

**Applies when:** recipe is loaded at launch.

---

### image-optimization

Images MUST be appropriately sized, compressed, and use platform-preferred formats.

**Applies when:** recipe displays images.

---

### caching-strategy

Frequently accessed remote data SHOULD use a caching strategy with defined invalidation.

**Applies when:** recipe fetches data from a remote source that is accessed repeatedly.

**Guidelines:**
- [Caching](agentic-cookbook://guidelines/networking/caching)

---

### progress-indication

Operations exceeding 200ms MUST show progress indication.

**Applies when:** recipe performs operations that may take a noticeable amount of time.

**Guidelines:**
- [Always Show Progress](agentic-cookbook://guidelines/ui/always-show-progress)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-28 | Mike Fullerton | Initial creation |
