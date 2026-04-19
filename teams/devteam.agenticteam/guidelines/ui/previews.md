---

id: 40ba1017-cec3-42f0-bd89-63a29eb3dd4d
title: "Previews"
domain: agentic-cookbook://guidelines/implementing/ui/previews
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "All UI components MUST include preview declarations for rapid visual verification during development. Previews should..."
platforms: 
  - kotlin
  - swift
tags: 
  - previews
  - ui
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
---

# Previews

All UI components MUST include preview declarations for rapid visual verification during development. Previews should cover all significant states (default, loading, error, empty, populated).

## Swift

All SwiftUI views MUST include `#Preview` blocks. Verification includes confirming previews render without crashes.

## Kotlin

All Compose components MUST include `@Preview` functions. Verification includes confirming preview functions compile.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
