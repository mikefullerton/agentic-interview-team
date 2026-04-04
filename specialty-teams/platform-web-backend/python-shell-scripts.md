---
name: python-shell-scripts
description: `main()` functions delegate to named functions — no inline logic in main; composable and testable structure
artifact: guidelines/language/python/shell-scripts.md
version: 1.0.0
---

## Worker Focus
`main()` functions delegate to named functions — no inline logic in main; composable and testable structure

## Verify
`main()` body contains only function calls; no inline if/for/try blocks in main; each logical step is a named function
