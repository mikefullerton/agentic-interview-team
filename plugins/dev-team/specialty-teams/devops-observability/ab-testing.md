---
name: ab-testing
description: Features that may need experimentation support variant assignment via `ExperimentProvider` interface (`variant(key) -> S...
artifact: guidelines/feature-management/ab-testing.md
version: 1.0.0
---

## Worker Focus
Features that may need experimentation support variant assignment via `ExperimentProvider` interface (`variant(key) -> String`); local default implementation with debug panel override

## Verify
`ExperimentProvider` interface used at call sites; debug panel can override variant assignment; no hardcoded variant strings in feature code; local default returns a deterministic variant
