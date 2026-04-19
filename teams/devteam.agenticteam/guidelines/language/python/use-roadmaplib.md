---

id: faa53b44-0de6-44bc-9064-c7a06462eaa8
title: "Use roadmap_lib"
domain: agentic-cookbook://guidelines/implementing/code-quality/use-roadmaplib
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Use functions from `roadmap_lib` for all roadmap operations (reading state, parsing frontmatter, finding steps, etc.)..."
platforms: []
languages:
  - python
tags: 
  - language
  - python
  - use-roadmaplib
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - new-module
---

# Use roadmap_lib

Functions from `roadmap_lib` MUST be used for all roadmap operations (reading state, parsing frontmatter, finding steps, etc.). Functionality that already exists in the library MUST NOT be reimplemented.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
