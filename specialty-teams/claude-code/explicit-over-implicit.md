---
name: explicit-over-implicit
description: Make dependencies visible — skills that need files should read them explicitly, not rely on ambient context; name things...
artifact: principles/explicit-over-implicit.md
version: 1.0.0
---

## Worker Focus
Make dependencies visible — skills that need files should read them explicitly, not rely on ambient context; name things for what they do; prefer clear parameter passing over ambient state; no hidden behavior or magic invocation paths

## Verify
All file dependencies listed explicitly in skill steps; no skills relying on undocumented ambient state; agent instructions say what to do, not how to "figure it out"; context injected explicitly rather than assumed to be present
