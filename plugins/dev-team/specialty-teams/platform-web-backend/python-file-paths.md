---
name: python-file-paths
description: `pathlib.Path` for all path operations, never `os.path` string concatenation; `Path.home()` for home-relative paths
artifact: guidelines/language/python/file-paths.md
version: 1.0.0
---

## Worker Focus
`pathlib.Path` for all path operations, never `os.path` string concatenation; `Path.home()` for home-relative paths

## Verify
No `os.path.join`, `os.path.exists`, or string `/` path concatenation; all path operations use `pathlib.Path`; imports include `from pathlib import Path`
