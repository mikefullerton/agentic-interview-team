---
name: testing
description: Every change needs tests, every bug fix needs a regression test; prioritize unit tests over integration; test state tran...
artifact: guidelines/testing/testing.md
version: 1.0.0
---

## Worker Focus
Every change needs tests, every bug fix needs a regression test; prioritize unit tests over integration; test state transitions, edge cases, serialization round-trips; avoid fragile UI tests — test component logic as units instead

## Verify
Test file exists for every implementation file; bug fix commits include a regression test; no UI-only tests for logic that can be unit-tested
