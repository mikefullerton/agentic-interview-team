---

id: 746b6b5e-11b9-48f7-a304-4b6755fd7f75
title: "Interface Cohesion"
domain: agentic-cookbook://guidelines/planning/code-quality/interface-cohesion
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Group files by their shared public API surface — types, protocols, and exported symbols that define a coherent contract."
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

# Interface Cohesion

A well-factored module exposes a coherent public surface. When multiple files jointly define, implement, or serve a single public API contract — a protocol and its default implementation, a set of co-exported types, or a shared base class and its required overrides — those files belong in the same scope group. This lens identifies clusters of files united by a shared public interface rather than by directory proximity alone.

## Signals and Indicators

**Public and exported declarations to locate:**

- Swift `public` / `open` classes, structs, protocols, and typealiases. Pay special attention to protocol + extension pairs — the extension often lives in a separate file but is inseparable from the protocol definition.
- Kotlin `interface` declarations in the same package as their primary implementors. `sealed class` hierarchies — the sealed parent and all its subclasses form a single interface unit.
- TypeScript `export` statements at the top level, particularly in `index.ts` barrel files that re-export from multiple implementation files. The barrel and everything it re-exports constitute one interface surface.
- C# `interface` definitions paired with their `abstract class` base implementations. `partial class` declarations spread across files — all partials of the same class belong together.
- Java `interface` + `abstract class` + primary implementation triads are a common pattern; treat them as one unit.

**Shared type usage:**

- Types that appear in the parameter or return position of multiple files' public functions — these types are load-bearing for the interface and belong with it.
- DTOs, request/response models, and error types that are defined in one file and consumed across many — they define a shared contract.
- Protocol/interface conformance declarations: a file that declares `extension Foo: BarProtocol` is coupled to both `Foo` and `BarProtocol`.

**Co-export patterns:**

- Barrel files (`index.ts`, `__init__.py`, `Public.swift`) that gather exports from multiple files — the barrel signals that those files are intended to be consumed together.
- Umbrella headers in C/Objective-C that include multiple sub-headers — the umbrella defines the public interface boundary.
- Re-export declarations (`export { A } from './a'; export { B } from './b'`) that assemble a unified API from parts.

**Versioned interfaces:**

- Files with version suffixes (`AuthServiceV2.swift`, `PaymentApiV3.kt`) paired with adapter or migration shims — these are part of the same interface evolution and belong together.

## Boundary Detection

1. **Protocol/interface + implementors form one unit.** If a file defines a protocol and a second file is its primary concrete implementation, they belong in the same scope group unless the implementation is independently large enough to warrant separation (50+ files).
2. **Barrel files define the interface boundary.** Everything a barrel re-exports is part of the same public surface. If the barrel re-exports from five subdirectories, those subdirectories share an interface and are candidates for a single scope group — unless they are large enough to warrant separate groups that share a common API layer.
3. **Shared types follow their primary consumer, not their definition file.** A `UserProfile` struct defined in `Models/` but used only by the `Auth` module belongs in the `Auth` scope group.
4. **Fragmented interfaces are a smell.** If the same logical interface is declared across three files with no organizing barrel, note this as a cohesion anomaly — it indicates the public surface has not been intentionally designed.
5. **Internal helpers are not interface.** Private/internal/file-private symbols do not contribute to interface cohesion; they contribute to implementation cohesion analyzed by `dependency-clusters`.

## Findings Format

```
INTERFACE COHESION FINDINGS
===========================

Public Interface Surfaces Identified:
  - <InterfaceName>
      Defining files: <list>
      Co-exported types: <list>
      Files implementing this interface: <list>
      Verdict: <e.g., "cohesive — all files serve the same public contract" | "fragmented — same interface split across unrelated directories">

Shared Types (used across 3+ files):
  - <TypeName> — defined in <file>, consumed by: <file list>

Barrel Files:
  - <path> — re-exports from: <list of source files/dirs>

Cohesion Anomalies:
  - <description of fragmented or incoherent interface>

Recommended Scope Group Candidates:
  - <InterfaceName> — <one-line rationale>
```

## Change History
