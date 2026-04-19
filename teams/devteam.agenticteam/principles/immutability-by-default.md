---
id: a7ce3621-2fed-478f-8767-b186014c5923
title: "Immutability by default"
domain: agentic-cookbook://principles/immutability-by-default
type: principle
version: 1.0.0
status: accepted
language: en
created: 2026-03-27
modified: 2026-03-27
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Mutable shared state is the root cause of most concurrency bugs. Default to immutable values; introduce mutability on..."
platforms: 
  - kotlin
  - swift
tags: 
  - immutability-by-default
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
---

# Immutability by default

Mutable shared state is the root cause of most concurrency bugs. Default to immutable values; introduce mutability only where necessary:

- Use `let` (Swift), `val` (Kotlin), `const` (JS/TS) by default
- Prefer value types (structs, data classes) over reference types
- Contain mutation behind clear boundaries (actors, StateFlow, useState)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
