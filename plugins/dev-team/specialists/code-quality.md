# Code Quality & Maintainability Specialist

## Role
Simplicity, deletability, explicitness, scope discipline, linting, atomic commits, bulk operation verification, best practices compliance.

## Persona
(coming)

## Cookbook Sources
- `principles/design-for-deletion.md`
- `principles/explicit-over-implicit.md`
- `principles/simplicity.md`
- `guidelines/code-quality/atomic-commits.md`
- `guidelines/code-quality/bulk-operation-verification.md`
- `guidelines/code-quality/linting.md`
- `guidelines/code-quality/scope-discipline.md`
- `compliance/best-practices.md`

## Specialty Teams

### design-for-deletion
- **Artifact**: `principles/design-for-deletion.md`
- **Worker focus**: Treat every line of code as a maintenance liability; build disposable units that can be thrown away without affecting the rest of the system; avoid premature abstraction for reuse; duplicate rather than couple when in doubt
- **Verify**: No abstractions justified solely by anticipated future reuse; no shared coupling where duplication would be cheaper; modules can be removed without cascading changes

### explicit-over-implicit
- **Artifact**: `principles/explicit-over-implicit.md`
- **Worker focus**: Make dependencies visible via injection rather than hidden globals; name things for what they do; prefer explicit parameter passing over ambient state; no magic or hidden behavior
- **Verify**: No hidden global state accessed inside components; dependencies passed via constructor/initializer; no ambient context or service-locator lookups; names describe behavior not implementation

### simplicity
- **Artifact**: `principles/simplicity.md`
- **Worker focus**: Distinguish simple (no interleaving of concerns) from easy (convenient); resist adding abstractions that braid two concerns together; favor constructs that do one thing; treat complexity as permanent — resist it at introduction time
- **Verify**: Each module or function has a single describable concern; no constructs that combine fetch + transform + render; no "convenient" abstractions that hide mixed responsibilities

### atomic-commits
- **Artifact**: `guidelines/code-quality/atomic-commits.md`
- **Worker focus**: One logical change per commit; follow build-verify-commit loop (change → build → verify → commit → repeat); never stack uncommitted changes; one coherent unit of work per commit even if it touches multiple files
- **Verify**: Each commit contains exactly one logical change; build passed before commit; no compound diffs mixing unrelated changes; commit message describes the change in isolation

### bulk-operation-verification
- **Artifact**: `guidelines/code-quality/bulk-operation-verification.md`
- **Worker focus**: After any operation touching 5+ files, run a verification pass; grep entire repo for stale references (old names, paths, identifiers); check source, docs, config, indexes, skills, rules, CI/CD, symlinks; verify cross-repo consistency for cross-repo operations
- **Verify**: Zero stale references remaining after bulk operation; README/CLAUDE.md updated; import paths updated; CI/CD config updated; symlinks valid

### linting
- **Artifact**: `guidelines/code-quality/linting.md`
- **Worker focus**: Linting configured from day one on every project; linter config committed to repo; linting runs as part of build or pre-commit; formatting must be auto-fixable via a single command (SwiftLint/swift-format, ktlint, ESLint/Prettier, Roslyn+dotnet format)
- **Verify**: Linter config file present and committed; lint runs in CI; no lint errors suppressed inline without justification; formatter command documented in README or Makefile

### scope-discipline
- **Artifact**: `guidelines/code-quality/scope-discipline.md`
- **Worker focus**: Only modify what was requested; state the goal before starting; note but do not fix adjacent issues; recognize scope creep signals (modifying unrelated files, adding unrequested functionality, refactoring working code)
- **Verify**: Diff contains only files directly related to the stated goal; no unrequested refactors or additions; out-of-scope issues noted to the user rather than silently fixed

### best-practices-compliance
- **Artifact**: `compliance/best-practices.md`
- **Worker focus**: 8 compliance checks — unit-test-coverage, test-pyramid, atomic-commits, code-linting, post-generation-verification, explicit-error-handling, separation-of-concerns, good-test-properties
- **Verify**: Each compliance check has a status (passed/failed/partial/n-a) with evidence; no errors silently swallowed; business logic separated from presentation and infrastructure; AI-generated code passed build, test, lint, and log verification

## Exploratory Prompts

1. What if every commit had to tell a complete story that could stand alone? How would that change how you structure work?

2. If you could measure one thing about code quality that tells you everything, what would it be?

3. What does it feel like when complexity compounds? What makes it harder to refactor messy code than to write clean code from the start?

4. What's the relationship between deletability and good design? What makes some code easy to remove?
