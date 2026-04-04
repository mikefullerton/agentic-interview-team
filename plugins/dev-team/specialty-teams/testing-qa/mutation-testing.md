---
name: mutation-testing
description: Run mutation testing before claiming tests are complete; platform tools: mutmut (Python), Stryker (TypeScript/JS/.NET), ...
artifact: guidelines/testing/mutation-testing.md
version: 1.0.0
---

## Worker Focus
Run mutation testing before claiming tests are complete; platform tools: mutmut (Python), Stryker (TypeScript/JS/.NET), Muter (Swift), Pitest (Kotlin/JVM); examine surviving mutants and write additional tests to kill them

## Verify
Mutation testing run and results reviewed; no surviving mutants in critical paths; mutation score documented or acceptable threshold met before marking test suite complete
