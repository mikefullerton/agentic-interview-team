---
name: property-based-testing
description: Use for parsers, serializers, data transformers, encoders/decoders, validators — anything where "for all valid inputs X,...
artifact: guidelines/testing/property-based-testing.md
version: 1.0.0
---

## Worker Focus
Use for parsers, serializers, data transformers, encoders/decoders, validators — anything where "for all valid inputs X, property Y holds"; platform tools: Hypothesis (Python), fast-check (TypeScript), FsCheck (.NET), jqwik (Kotlin/JVM), swift-testing parameterized (Swift)

## Verify
At least one property test per data transformation function; round-trip property tested for encode/decode pairs (`encode(decode(x)) == x`); preservation property tested for collection operations
