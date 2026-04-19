---
id: 793f491f-a352-4478-876d-7c5d871488f7
title: "YAGNI"
domain: agentic-cookbook://principles/yagni
type: principle
version: 1.0.0
status: accepted
language: en
created: 2026-03-27
modified: 2026-03-27
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Build for today's known requirements. Speculative generality adds code that must be maintained but delivers no curren..."
platforms: []
tags: 
  - yagni
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
---

# YAGNI

Build for today's known requirements. Speculative generality adds code that must be maintained but delivers no current value. If a future need materializes, the cost of adding it then is almost always lower than maintaining premature abstractions now.

- Before adding a parameter, config option, or extension point, confirm a current requirement demands it
- Delete dead code and unused abstractions — they are not "free" to keep around
- When someone says "we might need this later," treat that as a reason to wait, not a reason to build

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
