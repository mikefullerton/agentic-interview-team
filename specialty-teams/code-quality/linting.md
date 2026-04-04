---
name: linting
description: Linting configured from day one on every project; linter config committed to repo; linting runs as part of build or pre-...
artifact: guidelines/code-quality/linting.md
version: 1.0.0
---

## Worker Focus
Linting configured from day one on every project; linter config committed to repo; linting runs as part of build or pre-commit; formatting must be auto-fixable via a single command (SwiftLint/swift-format, ktlint, ESLint/Prettier, Roslyn+dotnet format)

## Verify
Linter config file present and committed; lint runs in CI; no lint errors suppressed inline without justification; formatter command documented in README or Makefile
