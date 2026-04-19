---

id: acbfc5ff-4482-4982-a893-b792da0fbe4f
title: "Deterministic IDs"
domain: agentic-cookbook://guidelines/implementing/data/deterministic-ids
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Always use the roadmap file's own UUID from its YAML frontmatter. Never generate random UUIDs. IDs must be determinis..."
platforms: []
languages:
  - python
tags: 
  - deterministic-ids
  - language
  - python
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - data-modeling
---

# Deterministic IDs

The roadmap file's own UUID from its YAML frontmatter MUST be used. Random UUIDs MUST NOT be generated. IDs MUST be deterministic and reproducible.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
