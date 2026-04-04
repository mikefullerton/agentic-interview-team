---
name: the-testing-workflow
description: Complete closed-loop workflow — write implementation, write unit tests (with property-based for data transforms), run te...
artifact: guidelines/testing/the-testing-workflow.md
version: 1.0.0
---

## Worker Focus
Complete closed-loop workflow — write implementation, write unit tests (with property-based for data transforms), run tests, validate test quality with mutation testing, kill surviving mutants, run security scan, run E2E verification; AI generates tests, deterministic tools validate them, AI closes gaps

## Verify
All 7 workflow steps executed in order; mutation testing results reviewed before declaring tests complete; security scan step not skipped; E2E verification covers critical user journeys
