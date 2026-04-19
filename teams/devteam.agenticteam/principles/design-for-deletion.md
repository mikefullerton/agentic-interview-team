---
id: 2aaf1727-aa36-41d1-a660-7dd0456e1d07
title: "Design for deletion"
domain: agentic-cookbook://principles/design-for-deletion
type: principle
version: 1.0.0
status: accepted
language: en
created: 2026-03-27
modified: 2026-03-27
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Every line of code is a maintenance liability. Build disposable software, not reusable software:"
platforms: []
tags: 
  - design-for-deletion
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
---

# Design for deletion

Every line of code is a maintenance liability. Build disposable software, not reusable software:

- Write code that is easy to throw away without affecting the rest of the system
- Treat lines of code as lines spent — deleting code reduces maintenance cost
- Do not abstract prematurely in pursuit of reuse
- When in doubt, duplicate rather than couple

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
