---
name: ab-testing
description: Features that may need experimentation support variant assignment via `ExperimentProvider` interface (`variant(key) -> S...
artifact: guidelines/feature-management/ab-testing.md
version: 1.0.0
---

## Worker Focus
Features that may need experimentation support variant assignment via `ExperimentProvider` interface (`variant(key) -> String`); local default implementation; debug panel override for manual variant selection

## Verify
Experimentable features implement `ExperimentProvider` interface; local default variant returns a valid value; debug panel allows variant override without code changes
