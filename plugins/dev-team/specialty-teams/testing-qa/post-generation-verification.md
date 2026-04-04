---
name: post-generation-verification
description: Every generated artifact must pass 6 steps — build (all platforms), test (full suite), lint (platform linter), log verif...
artifact: guidelines/testing/post-generation-verification.md
version: 1.0.0
---

## Worker Focus
Every generated artifact must pass 6 steps — build (all platforms), test (full suite), lint (platform linter), log verification (grep for expected log messages), accessibility audit (VoiceOver/TalkBack labels, tap targets, contrast), code review against best practices

## Verify
Build passes for all target platforms; all tests pass; linter reports no errors; log grep confirms expected output; accessibility tap targets meet minimums (44pt iOS, 48dp Android)
