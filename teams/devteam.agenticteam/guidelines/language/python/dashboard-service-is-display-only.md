---

id: 54317850-9536-4b9e-ac3a-a2ac5bc13ec6
title: "Dashboard service is display-only"
domain: agentic-cookbook://guidelines/implementing/ui/dashboard-service-is-display-only
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "The dashboard service is a generic API and UI layer. It has no knowledge of git, files, or roadmap structure. Agents ..."
platforms: []
languages:
  - python
tags: 
  - dashboard-service-is-display-only
  - language
  - python
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
  - new-module
---

# Dashboard service is display-only

The dashboard service is a generic API and UI layer. It MUST NOT have knowledge of git, files, or roadmap structure. Agents sync data to it; it MUST only display what it receives.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
