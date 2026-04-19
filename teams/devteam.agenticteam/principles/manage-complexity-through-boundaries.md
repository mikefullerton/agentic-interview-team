---
id: 555ad5e1-800f-4848-8c58-6f726bdcb42b
title: "Manage complexity through boundaries"
domain: agentic-cookbook://principles/manage-complexity-through-boundaries
type: principle
version: 1.0.0
status: accepted
language: en
created: 2026-03-27
modified: 2026-03-27
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Well-defined boundaries between subsystems let each side evolve independently. Define ports (interfaces) that describ..."
platforms: []
tags: 
  - manage-complexity-through-boundaries
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
---

# Manage complexity through boundaries

Well-defined boundaries between subsystems let each side evolve independently. Define ports (interfaces) that describe what the application needs. Use adapters to translate between external technologies and your ports. Test the core application without databases, UIs, or networks.

- Define each external dependency as a protocol the app owns, not a concrete type the vendor owns
- Keep adapter implementations thin — translate and delegate, never add business logic
- If two modules need to share a type, extract it into a shared contract rather than coupling the modules directly
- Verify boundaries by confirming core logic compiles and tests pass with no framework imports

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
