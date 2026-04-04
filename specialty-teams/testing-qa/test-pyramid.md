---
name: test-pyramid
description: 80% unit / 15% integration / 5% E2E; unit tests are fast and isolated; integration tests use real databases/filesystems/...
artifact: guidelines/testing/test-pyramid.md
version: 1.0.0
---

## Worker Focus
80% unit / 15% integration / 5% E2E; unit tests are fast and isolated; integration tests use real databases/filesystems/HTTP where practical; E2E reserved for critical user journeys only

## Verify
Test count ratios approximate 80/15/5; no E2E test for behavior coverable by unit test; if unit test can't cover behavior, integration test used before escalating to E2E
