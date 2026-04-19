---

id: a7192ade-023d-43b5-b68c-eb2b7024a3fd
title: "Purpose Classification"
domain: agentic-cookbook://guidelines/planning/code-quality/purpose-classification
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Classify every file by its primary reason for existing, and verify that each candidate scope group has a single coherent purpose."
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

# Purpose Classification

Every file exists for a reason. That reason — the primary thing it does — is its purpose. Scope groups with a clear, singular purpose are cohesive and independently understandable. Scope groups whose files serve multiple unrelated purposes are incoherent and should be split. This lens classifies every file by its primary purpose and checks whether candidate scope groups are purpose-coherent.

## Signals and Indicators

**Purpose categories — classify each file into exactly one primary category:**

**UI Presentation** — code whose primary job is to display data to the user and translate user input into events. Indicators: `UIView`, `UIViewController`, React component, Composable, Blazor `.razor`, `Activity`, `Fragment`, `WPF UserControl`, layout XML/XAML. The deciding question: does this file exist to show something on screen?

**Data Transformation** — code whose primary job is to convert data from one form to another. Indicators: mappers (`UserMapper`, `toDTO()`, `fromJson()`), parsers, serializers/deserializers, formatters, encoders/decoders, validators that transform input into validated types. Does this file exist to reshape data?

**Orchestration/Coordination** — code whose primary job is to coordinate other components to fulfill a use case. Indicators: use cases, interactors, service facade objects, coordinators, workflow managers, application services. Does this file exist to sequence the work of other components?

**Persistence/Storage** — code whose primary job is to read from and write to durable storage. Indicators: repository implementations, DAO objects, Core Data managed object contexts, Room DAOs, Entity Framework `DbContext` subclasses, file system read/write operations, `UserDefaults`/`SharedPreferences` access. Does this file exist to make data survive process termination?

**Communication/Networking** — code whose primary job is to send and receive data over a network. Indicators: API client classes, `URLSession` wrappers, `Retrofit` interfaces, `axios` instances, `HttpClient` usage, WebSocket client/server, GraphQL client. Does this file exist to move data across a network boundary?

**Configuration** — code whose primary job is to supply settings, constants, or environment values that parameterize other code. Indicators: constants files, config structs, environment variable readers, feature flag definitions, app configuration objects, build-time compile constants. Does this file exist to hold values that control how other code behaves?

**Testing Infrastructure** — code that exists to support testing of other code but is not itself a test. Indicators: mocks, stubs, fakes, test fixtures, factory helpers, test utilities, `XCTestCase` helpers, `MockK` setup utilities, test data builders. Does this file exist to make other code testable?

**Build Tooling** — code that exists to support the build process. Indicators: build scripts, code generators, Gradle plugins, Webpack configuration, Swift Package Manager plugins, lint rules, pre-commit hooks. Does this file exist to produce the artifact, not to be in it?

**Security/Auth** — code whose primary job is to authenticate, authorize, encrypt, or protect. Indicators: login flows, token management, OAuth flows, cryptographic operations, permission checks, certificate pinning, secure storage wrappers. Does this file exist to control who can do what?

**Analytics/Observability** — code whose primary job is to record what the application does for measurement or debugging. Indicators: analytics event definitions, tracking calls, metric collectors, logging facades, crash reporting setup, tracing instrumentation. Does this file exist to make the application observable?

**Domain Model** — code whose primary job is to represent domain concepts and their rules. Indicators: entity classes with business logic, value objects, domain events, aggregate roots, domain service objects (pure business logic, no I/O). Does this file exist to encode what the business concepts ARE and what rules govern them?

**Multi-purpose files (mixed concerns):**

- A file that presents UI AND calls the network directly is mixing UI Presentation with Communication/Networking
- A file that holds both business logic AND persistence calls is mixing Domain Model with Persistence/Storage
- A file that orchestrates a use case AND contains networking code is mixing Orchestration with Communication/Networking

Mixed-purpose files are a smell — document them and recommend refactoring, but do not create a mixed-purpose scope group to accommodate them.

## Boundary Detection

1. **Purpose-coherent groups are correctly scoped.** If every file in a candidate scope group has the same primary purpose, the group is coherent. Different purposes within the same group indicate either misclassification or a need to split.
2. **Each scope group should have one sentence purpose.** Test: can you complete "This scope group exists to ___" with a single clear answer? If the answer requires "and also", the group conflates concerns.
3. **Mixed-purpose files mark the fault line.** A file that mixes UI and networking is a symptom — the fault line is between those two purposes. Recommend splitting the file along that line.
4. **Configuration is rarely its own scope group.** Configuration files belong with the components they configure, unless they configure the entire application (in which case they belong in an application bootstrap scope group).
5. **Testing infrastructure belongs adjacent to its subject.** Test mocks and fakes belong in the same scope group as the types they mock, or in a shared test infrastructure scope group if used across multiple groups.
6. **Build tooling is always its own scope group.** Build scripts, code generators, and Gradle/Webpack configuration are not part of any runtime scope group — they form a `Build Tooling` scope group that is excluded from runtime analysis.

## Findings Format

```
PURPOSE CLASSIFICATION FINDINGS
=================================

File Classification Summary:
  UI Presentation:         <n> files
  Data Transformation:     <n> files
  Orchestration:           <n> files
  Persistence/Storage:     <n> files
  Communication/Network:   <n> files
  Configuration:           <n> files
  Testing Infrastructure:  <n> files
  Build Tooling:           <n> files
  Security/Auth:           <n> files
  Analytics/Observability: <n> files
  Domain Model:            <n> files
  Mixed/Unclear:           <n> files

Candidate Group Coherence:
  - <GroupName>: <"purpose-coherent: <category>" | "mixed: <category list> — recommend split">

Mixed-Purpose Files:
  - <file> — mixes: <category 1> and <category 2>
    Recommended split: <brief description>

Build Tooling Files (excluded from runtime scope groups):
  - <file list>

Recommended Scope Group Candidates:
  - <Name> — purpose: <category>, <one-line rationale>
```

## Change History
