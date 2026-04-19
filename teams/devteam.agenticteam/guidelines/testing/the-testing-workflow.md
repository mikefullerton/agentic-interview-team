---

id: 8ab7452a-09b8-4f4e-abfc-f7fd700765db
title: "The Testing Workflow"
domain: agentic-cookbook://guidelines/testing/the-testing-workflow
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "The recommended Claude Code testing workflow, combining all tools:"
platforms: 
  - python
  - swift
  - typescript
  - web
tags: 
  - testing
  - the-testing-workflow
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - writing-tests
  - pre-pr
---

# The Testing Workflow

The recommended Claude Code testing workflow, combining all tools:

1. **Write implementation code**
2. **Write unit tests** — informed by property-based testing for data transformations
3. **Run tests** — `pytest` / `swift test` / `npm test` / `dotnet test`
4. **Validate test quality** — `mutmut run` / `npx stryker run` / `muter` / `dotnet stryker`
5. **Kill surviving mutants** — additional tests MUST be written targeting gaps
6. **Security scan** — `semgrep scan` + `bandit` / `pip-audit` / `npm audit` MUST be run
7. **E2E verification** — Playwright for web UIs, platform test runners for native

This creates a closed loop: AI generates tests, deterministic tools validate those tests
actually catch bugs, AI writes more tests to close gaps.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
