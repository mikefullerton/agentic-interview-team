---

id: d991b992-07aa-47b9-9d36-4fd1ca81435f
title: "A/B testing"
domain: agentic-cookbook://guidelines/implementing/feature-management/ab-testing
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Features that may need experimentation SHOULD support variant assignment via an `ExperimentProvider` interface (`vari..."
platforms: []
tags: 
  - ab-testing
  - feature-management
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - feature-flags
  - logging
---

# A/B testing

Features that may need experimentation SHOULD support variant assignment via an `ExperimentProvider` interface (`variant(key) -> String`). Local default with debug panel override.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
