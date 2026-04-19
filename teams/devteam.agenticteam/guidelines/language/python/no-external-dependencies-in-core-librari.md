---

id: dca53225-bd2b-4a11-8abb-5226e05de4a7
title: "No external dependencies in core libraries"
domain: agentic-cookbook://guidelines/implementing/code-quality/no-external-dependencies-in-core-librari
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "`roadmap_lib` uses the standard library only. Do not add PyYAML, requests, or other third-party packages to core libr..."
platforms: []
languages:
  - python
tags: 
  - language
  - no-external-dependencies-in-core-librari
  - python
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - dependency-management
  - new-module
---

# No external dependencies in core libraries

`roadmap_lib` uses the standard library only. Third-party packages (PyYAML, requests, etc.) MUST NOT be added to core library code. This keeps the library portable and installable without dependency management.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
