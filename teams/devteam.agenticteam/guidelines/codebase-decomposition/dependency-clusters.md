---

id: 4de09db8-b6fe-4211-b7e4-c95619a12141
title: "Dependency Clusters"
domain: agentic-cookbook://guidelines/planning/code-quality/dependency-clusters
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Identify scope groups by measuring internal coupling density versus external coupling — files that import each other heavily belong together."
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
  - code-review
  - new-module
---

# Dependency Clusters

The import graph is the most objective structural signal in a codebase. Files that frequently import each other form clusters with high internal cohesion. Files with few internal imports and many external imports are loosely coupled and may be candidates for separate scope groups. This lens builds a coarse import graph and identifies clusters with high internal coupling density — these are natural scope group candidates.

## Signals and Indicators

**Import statement forms by platform:**

- Swift: `import ModuleName` at file top; `@_implementationOnly import` for private dependencies; within a module, `import class ModuleName.TypeName` for targeted imports
- Kotlin: `import com.example.package.ClassName` statements; star imports (`import com.example.package.*`) suggest tight coupling to an entire package
- TypeScript/JavaScript: `import { A, B } from './relative/path'` for internal; `import { C } from 'npm-package'` for external. Relative paths (starting with `./` or `../`) are internal; bare specifiers are external.
- C#: `using Namespace.Sub;` directives — internal vs external determined by namespace prefix matching the project's root namespace
- Java: `import com.example.*` — internal vs external by package prefix
- C/C++: `#include "local.h"` (quoted — local/internal) vs `#include <system.h>` (angle bracket — system/external)
- Go: import paths — module-local paths share the module prefix from `go.mod`; external paths reference a different module

**Coupling metrics to compute:**

- **Internal coupling:** count of import relationships between files within a candidate group
- **External coupling:** count of import relationships from files in the candidate group to files outside it
- **Coupling ratio:** internal / (internal + external). Ratios above 0.6 indicate a cohesive cluster; below 0.3 indicates a loosely coupled file that may not belong.
- **Fan-in:** number of files that import a given file — high fan-in files are likely shared infrastructure or cross-cutting concerns (see `cross-cutting-detection`)
- **Fan-out:** number of files a given file imports — high fan-out files are often orchestrators or aggregators

**Dependency direction:**

- Identify the direction of dependencies: do files in directory A import files in directory B, or vice versa? Unidirectional dependency flows suggest a layered architecture where the two directories belong in separate scope groups.
- Bidirectional dependencies (A imports B and B imports A) indicate either tight cohesion (same scope group) or a design problem (circular dependency that should be resolved).

**Circular dependencies:**

- Note any import cycles — these are candidates for refactoring, but in the short term they force the cyclic files into the same scope group since they cannot be independently deployed.

## Boundary Detection

1. **High internal coupling ratio (>0.6) = strong scope group candidate.** If 80% of a directory's imports are within the same directory, it is self-contained.
2. **Low coupling ratio (<0.3) = likely belongs elsewhere.** A file that imports mostly from other directories is probably a leaf consumer or a shared utility — consider merging it into the scope group it depends on most.
3. **Unidirectional dependency = separate scope groups.** If layer A only imports layer B (never the reverse), A and B are separate concerns even if they live near each other.
4. **High fan-in files are shared infrastructure.** A file imported by 10+ other files across multiple candidate groups is a cross-cutting dependency — flag it for `cross-cutting-detection` rather than assigning it to one group.
5. **Circular dependencies force co-location.** Files in a cycle must remain in the same scope group until the cycle is resolved. Document the cycle as a refactoring target.
6. **Star imports inflate apparent coupling.** A `import com.example.util.*` may only use one symbol — do not count star imports as full coupling without verifying symbol usage.

## Findings Format

```
DEPENDENCY CLUSTERS FINDINGS
=============================

Import Graph Summary:
  Total files analyzed: <n>
  Total import relationships: <n>
  Internal import relationships: <n> (<pct>%)
  External import relationships: <n> (<pct>%)

Identified Clusters:
  - Cluster: <name or directory path>
      Files: <count>
      Internal coupling ratio: <0.0–1.0>
      External dependencies: <list of external targets>
      Verdict: <"cohesive" | "loosely coupled" | "mixed">

High Fan-In Files (shared infrastructure candidates):
  - <file> — imported by <n> files across <m> directories

Circular Dependencies:
  - <file A> ↔ <file B> [↔ <file C>] — forces co-location

Coupling Anomalies:
  - <description — e.g., "AuthManager imports 8 files from PaymentModule, suggesting misplaced responsibility">

Recommended Scope Group Candidates:
  - <ClusterName> — internal coupling ratio <x>, <one-line rationale>
```

## Change History
