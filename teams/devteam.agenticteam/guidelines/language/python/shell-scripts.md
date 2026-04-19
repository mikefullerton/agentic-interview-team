---

id: e9e60a7e-4e15-40e7-b730-fc2e311df1af
title: "Shell scripts"
domain: agentic-cookbook://guidelines/implementing/code-quality/shell-scripts
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Shell script `main()` functions must only call other functions — no inline logic. Keep scripts composable and testable."
platforms: []
languages:
  - python
tags: 
  - language
  - python
  - shell-scripts
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - new-module
  - configuration
---

# Shell scripts

Shell script `main()` functions MUST only call other functions — no inline logic. Scripts MUST be kept composable and testable.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
