---
id: f6679a9d-e90e-4fc6-ac4c-0696851af484
title: "Composition over inheritance"
domain: agentic-cookbook://principles/composition-over-inheritance
type: principle
version: 1.0.0
status: accepted
language: en
created: 2026-03-27
modified: 2026-03-27
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Default to composing behaviors from small, focused pieces. Use inheritance only for genuine 'is-a' relationships, and..."
platforms: []
tags: 
  - composition-over-inheritance
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
---

# Composition over inheritance

Default to composing behaviors from small, focused pieces. Use inheritance only for genuine "is-a" relationships, and even then sparingly. Prefer protocols/interfaces over base classes. When extending behavior, wrap rather than subclass.

- When tempted to subclass, ask: "Is this truly an 'is-a' relationship, or am I just reusing code?"
- Extract shared behavior into protocols or standalone functions instead of a base class
- Wrap an existing type with a new type to add behavior rather than extending the inheritance chain

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
