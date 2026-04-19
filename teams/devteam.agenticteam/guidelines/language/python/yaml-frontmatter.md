---

id: 4c070e8f-332c-4831-95a1-d0776e7b7ce8
title: "YAML frontmatter"
domain: agentic-cookbook://guidelines/implementing/code-quality/yaml-frontmatter
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Parse YAML frontmatter with the built-in frontmatter parser in `roadmap_lib`. Do not add a PyYAML dependency. The par..."
platforms: []
languages:
  - python
tags: 
  - language
  - python
  - yaml-frontmatter
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - data-modeling
  - configuration
---

# YAML frontmatter

The built-in frontmatter parser in `roadmap_lib` MUST be used for parsing YAML frontmatter. A PyYAML dependency MUST NOT be added. The parser handles the `---` delimited frontmatter block at the top of markdown files.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
