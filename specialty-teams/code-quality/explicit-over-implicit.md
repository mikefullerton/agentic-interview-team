---
name: explicit-over-implicit
description: Make dependencies visible via injection rather than hidden globals; name things for what they do; prefer explicit parame...
artifact: principles/explicit-over-implicit.md
version: 1.0.0
---

## Worker Focus
Make dependencies visible via injection rather than hidden globals; name things for what they do; prefer explicit parameter passing over ambient state; no magic or hidden behavior

## Verify
No hidden global state accessed inside components; dependencies passed via constructor/initializer; no ambient context or service-locator lookups; names describe behavior not implementation
