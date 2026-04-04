---
name: test-doubles
description: Use Martin Fowler's taxonomy (Dummy/Stub/Spy/Mock/Fake); prefer fakes over mocks — fakes exercise real behavior; never m...
artifact: guidelines/testing/test-doubles.md
version: 1.0.0
---

## Worker Focus
Use Martin Fowler's taxonomy (Dummy/Stub/Spy/Mock/Fake); prefer fakes over mocks — fakes exercise real behavior; never mock what you don't own — wrap external dependencies behind your own interface first

## Verify
In-memory fakes used for databases/queues where possible; no mocks of third-party APIs directly (only mock your own interface); platform-appropriate mock library used (NSubstitute/.NET, MockK/Kotlin, pytest-mock/Python, vitest/TS)
