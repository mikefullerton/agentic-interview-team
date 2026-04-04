---
name: python-type-hints
description: Type hints welcome but not required; Python 3.9 compatibility — use `from __future__ import annotations` or `typing` mod...
artifact: guidelines/language/python/type-hints.md
version: 1.0.0
---

## Worker Focus
Type hints welcome but not required; Python 3.9 compatibility — use `from __future__ import annotations` or `typing` module forms; avoid `list[str]` syntax without `__future__` import

## Verify
No 3.10+ syntax without compatibility guard; `from __future__ import annotations` present if modern syntax used; `Optional[str]` or `str | None` (with guard) used correctly
