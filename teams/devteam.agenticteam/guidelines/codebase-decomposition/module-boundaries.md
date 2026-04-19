---

id: 51038675-205b-4752-b826-4081b3729359
title: "Module Boundaries"
domain: agentic-cookbook://guidelines/planning/code-quality/module-boundaries
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Identify scope group candidates by locating explicit build targets, package manifests, and declared module boundaries."
platforms:
  - csharp
  - ios
  - kotlin
  - typescript
  - web
  - windows
tags:
  - codebase-decomposition
depends-on: []
related: []
references: []
triggers:
  - new-module
  - code-review
---

# Module Boundaries

Build systems and package managers formalize the boundaries developers intended. When a developer declares a build target, package, or module, they are encoding a structural decision about what belongs together. This lens reads those declarations directly rather than inferring them from file proximity.

## Signals and Indicators

**Build manifests to locate:**

- `Package.swift` (Swift Package Manager) — each `.target()` and `.testTarget()` declaration names an explicit module with a defined source directory
- `build.gradle` / `build.gradle.kts` (Gradle) — top-level `apply plugin:` blocks and subproject includes in `settings.gradle` mark module roots; `implementation`/`api` vs `compileOnly` dependency configurations reveal visibility intent
- `package.json` (Node/npm/yarn) — the `name` field and `exports` map define the public surface; workspaces in a monorepo root list all sub-packages
- `*.csproj` / `*.sln` (MSBuild) — each `.csproj` is a distinct assembly; solution file project references encode the dependency graph
- `Podfile` / `podspec` (CocoaPods) — each podspec is a distributable module boundary
- `MODULE.bazel` / `BUILD` / `BUILD.bazel` (Bazel) — `cc_library`, `swift_library`, `kt_jvm_library` rules define fine-grained build units
- `Cargo.toml` (Rust) — `[workspace]` members and `[lib]`/`[[bin]]` sections define crate boundaries
- `go.mod` (Go) — each module root is a deployable unit; subdirectory `package` declarations name internal groupings

**Directory naming conventions:**

- Directories named `core`, `common`, `shared`, or `util` at the root of a module often represent deliberate cross-cutting infrastructure — note but do not automatically split them
- Directories named after product features (`auth`, `payments`, `checkout`) suggest feature-module organization
- A `modules/` or `packages/` top-level directory almost always signals a monorepo with multiple independent scopes

**Access control declarations:**

- Swift `internal` vs `public` vs `package` keywords on types and functions
- Kotlin `internal` visibility modifier
- TypeScript `export` statements in `index.ts` barrel files
- C# `internal` vs `public` class visibility
- Java package-private (default) vs `public` visibility

## Boundary Detection

Each independently declared build target or package is a primary scope group candidate. Apply these rules:

1. **One target, one candidate.** If the build system declares it separately, treat it as a candidate scope group regardless of size. A 3-file Swift target is still a distinct module.
2. **Merge trivial wrappers.** If a target contains only re-exports of another target with no logic of its own, it may belong with the target it wraps.
3. **Split large monolithic targets.** A single build target containing 200+ files likely conflates multiple concerns. Flag for secondary analysis using `interface-cohesion` and `dependency-clusters` lenses.
4. **Test targets follow their main target.** `AuthTests` belongs with `Auth` — do not create a separate scope group for test targets unless they test multiple main targets.
5. **Vendor/third-party directories are excluded.** `node_modules/`, `Pods/`, `vendor/`, `.build/` — these are external dependencies, not scope groups.

## Findings Format

```
MODULE BOUNDARIES FINDINGS
==========================

Build System: <e.g., Swift Package Manager, Gradle, npm workspaces>
Manifest Files Found: <list with paths>

Declared Modules:
  - <ModuleName> (<path>) — <file count> files, <dependency count> declared dependencies
  - ...

Anomalies:
  - <ModuleName>: <reason — e.g., "single target with 300+ files, likely conflates concerns">
  - ...

Recommended Scope Group Candidates:
  - <ModuleName> — <one-line rationale>
  - ...
```

## Change History
