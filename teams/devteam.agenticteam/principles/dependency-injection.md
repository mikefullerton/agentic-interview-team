---
id: a2b79b0e-7d2c-44f5-b139-abc9cf47d1f5
title: "Dependency injection"
domain: agentic-cookbook://principles/dependency-injection
type: principle
version: 1.0.0
status: accepted
language: en
created: 2026-03-27
modified: 2026-03-27
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "A component should receive its dependencies from the outside, not construct them internally:"
platforms: []
tags: 
  - dependency-injection
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
---

# Dependency injection

A component should receive its dependencies from the outside, not construct them internally:

- Pass services via constructor/initializer parameters or protocol properties
- Never instantiate a concrete service inside the component that uses it
- Use protocol/interface types for dependencies, not concrete types
- Avoid service locator pattern (hidden global lookup)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
