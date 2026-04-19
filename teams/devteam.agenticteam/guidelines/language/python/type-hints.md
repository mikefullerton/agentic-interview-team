---

id: 82072abf-0ece-42da-805d-3cb15ce7921d
title: "Type hints"
domain: agentic-cookbook://guidelines/implementing/code-quality/type-hints
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Type hints are welcome but not required. Maintain Python 3.9 compatibility — use `from __future__ import annotations`..."
platforms: 
  - python
languages:
  - python
tags: 
  - language
  - python
  - type-hints
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - new-module
  - code-review
---

# Type hints

Type hints MAY be used but are not required. Python 3.9 compatibility MUST be maintained — use `from __future__ import annotations` or `typing` module forms (e.g., `list[str]` requires 3.9+, `Optional[str]` works everywhere).

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
