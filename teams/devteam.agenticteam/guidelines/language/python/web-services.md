---

id: 06c2a767-cd24-4527-b939-df44161d7025
title: "Web services"
domain: agentic-cookbook://guidelines/implementing/networking/web-services
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Use Flask for web services. The dashboard service runs on Flask with a REST API and SSE/polling for live updates."
platforms: 
  - python
  - web
languages:
  - python
tags: 
  - language
  - python
  - web-services
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - api-integration
  - new-module
---

# Web services

Flask MUST be used for web services. The dashboard service runs on Flask with a REST API and SSE/polling for live updates.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
