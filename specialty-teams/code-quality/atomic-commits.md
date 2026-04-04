---
name: atomic-commits
description: One logical change per commit; follow build-verify-commit loop (change → build → verify → commit → repeat); never stack ...
artifact: guidelines/code-quality/atomic-commits.md
version: 1.0.0
---

## Worker Focus
One logical change per commit; follow build-verify-commit loop (change → build → verify → commit → repeat); never stack uncommitted changes; one coherent unit of work per commit even if it touches multiple files

## Verify
Each commit contains exactly one logical change; build passed before commit; no compound diffs mixing unrelated changes; commit message describes the change in isolation
