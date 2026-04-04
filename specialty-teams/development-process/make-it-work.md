---
name: make-it-work
description: Sequential phases — correctness first (common case working), then refactor for clarity and edge cases, then optimize onl...
artifact: principles/make-it-work-make-it-right-make-it-fast.md
version: 1.0.0
---

## Worker Focus
Sequential phases — correctness first (common case working), then refactor for clarity and edge cases, then optimize only what measurement proves is slow; never skip phase 2 to jump directly to performance optimization

## Verify
Code handles the common case correctly before refactoring; edge cases and error handling addressed in phase 2 before any performance work; performance optimizations are measurement-driven, not speculative
