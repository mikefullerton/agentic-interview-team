---

id: db58f79d-1040-4bb2-a862-93ebd390ee12
title: "Mutation Testing"
domain: agentic-cookbook://guidelines/testing/mutation-testing
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Mutation testing validates that your tests actually catch bugs — not just achieve coverage."
platforms: 
  - csharp
  - kotlin
  - python
  - swift
  - typescript
tags: 
  - mutation-testing
  - testing
depends-on: []
related: []
references: 
  - https://github.com/boxed/mutmut
  - https://github.com/muter-mutation-testing/muter
  - https://pitest.org/
  - https://stryker-mutator.io/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - writing-tests
  - pre-pr
---

# Mutation Testing

Mutation testing validates that your tests actually catch bugs — not just achieve coverage.

**How it works:** The tool mutates your source code (e.g., changes `<` to `<=`, `True` to
`False`, deletes a line) and re-runs your tests. If tests still pass, the mutant "survived"
— meaning your tests have a blind spot.

**The closed loop:**
1. Write tests
2. Run mutation testing
3. Examine surviving mutants
4. Write additional tests to kill surviving mutants — all surviving mutants MUST be addressed
5. Repeat until mutation score is acceptable

**Mutation testing MUST be run before claiming "tests are complete."**

**Platform tools:**

| Platform | Tool | Install | Run |
|----------|------|---------|-----|
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| Python | [mutmut](https://github.com/boxed/mutmut) | `pip install mutmut` | `mutmut run` |
| TypeScript/JS | [Stryker](https://stryker-mutator.io/) | `npm i -g stryker-cli` | `npx stryker run` |
| .NET | [Stryker.NET](https://stryker-mutator.io/) | `dotnet tool install -g dotnet-stryker` | `dotnet stryker` |
| Swift | [Muter](https://github.com/muter-mutation-testing/muter) | `brew install muter-mutation-testing/formulae/muter` | `muter` |
| Kotlin/JVM | [Pitest](https://pitest.org/) | Gradle/Maven plugin | `./gradlew pitest` |

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
