---
id: 425271ea-92b6-4df6-9a83-94795f1be377
title: "Fail fast"
domain: agentic-cookbook://principles/fail-fast
type: principle
version: 1.0.0
status: accepted
language: en
created: 2026-03-27
modified: 2026-03-27
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Invalid state should be detected and surfaced immediately at the point of origin, not propagated silently:"
platforms: []
tags: 
  - fail-fast
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
---

# Fail fast

Invalid state should be detected and surfaced immediately at the point of origin, not propagated silently:

- Use assertions and preconditions in debug builds
- Validate inputs at system boundaries
- Return typed errors rather than swallowing exceptions
- Never use empty catch blocks
- In production, fail gracefully with clear messages; in debug, fail loudly

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
