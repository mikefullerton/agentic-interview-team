---

id: ccffa426-5556-4bbe-8dd6-b43c8e195f64
title: "Property-Based Testing"
domain: agentic-cookbook://guidelines/testing/property-based-testing
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "When to use: parsers, serializers, data transformers, encoders/decoders, validators — anything"
platforms: 
  - csharp
  - kotlin
  - python
  - swift
  - typescript
tags: 
  - property-based-testing
  - testing
depends-on: []
related: []
references: 
  - https://fscheck.github.io/FsCheck/
  - https://github.com/HypothesisWorks/hypothesis
  - https://github.com/dubzzz/fast-check
  - https://jqwik.net/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - writing-tests
---

# Property-Based Testing

When to use: parsers, serializers, data transformers, encoders/decoders, validators — anything
where "for all valid inputs X, property Y holds."

**The principle:** Instead of testing specific examples, describe properties of the output
and let the framework generate hundreds of random inputs to try to falsify them.

**Platform tools:**

| Platform | Library | Install |
|----------|---------|---------|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Python | [Hypothesis](https://github.com/HypothesisWorks/hypothesis) | `pip install hypothesis` |
| TypeScript/JS | [fast-check](https://github.com/dubzzz/fast-check) | `npm install fast-check` |
| Swift | `@Test(arguments:)` (parameterized) | Built into swift-testing |
| .NET | [FsCheck](https://fscheck.github.io/FsCheck/) | `dotnet add package FsCheck` |
| Kotlin/JVM | [jqwik](https://jqwik.net/) | Gradle/Maven dependency |

**At least one property test MUST be written per data transformation function.** Examples:

- `encode(decode(x)) == x` (round-trip)
- `sort(xs).length == xs.length` (preservation)
- `parse(serialize(obj)).fields == obj.fields` (fidelity)

```python
from hypothesis import given
import hypothesis.strategies as st

@given(st.text())
def test_encode_decode_roundtrip(s):
    assert decode(encode(s)) == s
```

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
