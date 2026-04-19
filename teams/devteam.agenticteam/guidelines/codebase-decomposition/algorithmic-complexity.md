---

id: 02301325-6676-4b89-ac9f-e2cfe99a4172
title: "Algorithmic Complexity"
domain: agentic-cookbook://guidelines/planning/code-quality/algorithmic-complexity
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Characterize the computational profile of each candidate scope group by identifying dominant algorithms, data structures, and complexity characteristics."
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
  - performance-optimization
---

# Algorithmic Complexity

Not all code is computationally equivalent. A scope group dominated by UI layout has a different performance profile, testing strategy, and optimization approach than one that implements graph search or real-time signal processing. This lens characterizes the computational profile of each candidate scope group — what algorithms and data structures appear, what time and space complexity the code implies, and what engineering concerns follow from those choices.

## Signals and Indicators

**Sorting and search patterns:**

- Explicit sort calls with custom comparators — note whether the comparator is simple (field comparison) or compound (multi-key, weighted)
- Binary search implementations or calls to `binarySearch`, `lower_bound`, `upper_bound` — implies sorted input requirement
- Linear scan patterns over large collections — potential O(n) performance risk
- Priority queue usage (`PriorityQueue`, `Heap`, `sorted` sets) — implies ordering-sensitive processing

**Graph and tree traversals:**

- Explicit adjacency list or matrix construction
- BFS/DFS implementations — note cycle detection, visited sets
- Tree traversal patterns — in-order, pre-order, post-order, level-order
- Shortest path algorithms — Dijkstra, Bellman-Ford, A*
- Topological sort — implies dependency graph processing

**Caching and memoization:**

- `NSCache`, `LRUCache`, dictionary-as-cache patterns with explicit eviction logic
- `@cached_property`, `lazy var`, `lazy` computed properties — single-computation caches
- Memoization wrappers — functions that store prior results indexed by input
- Cache invalidation logic — expiry timestamps, version keys, dependency tracking
- Write-through vs write-back cache patterns

**Data structure choices:**

- Hash maps / dictionaries — O(1) lookup; note when used for frequency counting, grouping, or deduplication
- Sets for membership testing — note when used to eliminate duplicates from a stream
- Queues and deques — FIFO processing, sliding window patterns
- Linked lists — unusual in high-level languages; presence often indicates specialized ordering or O(1) insert/delete requirements
- Bloom filters or probabilistic structures — indicates performance-critical membership testing
- Tries — prefix search, autocomplete, routing tables
- Segment trees, Fenwick trees — range query optimization

**Recursion:**

- Deep recursion without tail-call optimization — stack overflow risk in large inputs
- Mutually recursive functions — complex control flow, harder to profile
- Trampoline patterns — recursive logic rewritten iteratively for stack safety

**Nested loops and complexity indicators:**

- Double nested loops over the same collection — O(n²) risk
- Triple or deeper nesting — O(n³) or worse; flag immediately
- Early-exit conditions (`break`, `guard`, `return`) that may redeem apparent O(n²) to amortized O(n)
- Outer loop over data, inner loop over configuration — often O(n×m) where m is small and bounded

**Parallelism and concurrency in computation:**

- `DispatchQueue.concurrentPerform`, `parallel()`, `ParallelStream`, `PLINQ`, `async/await` over collections — parallel computation patterns
- GPU compute (Metal, Vulkan, WebGPU compute shaders) — highly parallel numeric computation
- SIMD operations — vectorized arithmetic

**Numeric and signal processing:**

- Floating point accumulation patterns — summation, running averages; note precision concerns
- FFT or frequency domain processing
- Matrix multiplication — note if using accelerated libraries (Accelerate, BLAS, NumPy)
- Statistical computation — mean, variance, standard deviation, percentile calculation

## Boundary Detection

1. **High-complexity algorithms warrant their own scope group.** Code implementing O(n log n) or worse algorithms on large datasets is a distinct engineering concern — performance optimization, testing with large inputs, and benchmarking apply specifically to it.
2. **Caching layers are scope group candidates.** A caching subsystem with its own eviction policy, invalidation logic, and hit/miss tracking is a meaningful independent component.
3. **Computational code should not be mixed with I/O.** Files that mix algorithm implementation with network calls or file system access conflate two different concerns — note this as a design smell.
4. **Simple CRUD code is not a boundary signal.** Code that maps data structures to/from persistence formats and performs no interesting computation is not algorithmically significant — its boundaries come from `module-boundaries` or `purpose-classification`.
5. **Parallel computation implies a concurrency concern.** Code using parallel execution primitives has distinct testing requirements (race conditions, thread safety) and likely belongs in its own scope group or must be flagged as a concurrency concern.

## Findings Format

```
ALGORITHMIC COMPLEXITY FINDINGS
================================

Dominant Algorithms by Candidate Group:
  - <Group/Directory>:
      Algorithms: <list — e.g., "BFS graph traversal", "LRU cache with doubly linked list">
      Data structures: <list — e.g., "hash map for deduplication", "min-heap for scheduling">
      Complexity: <e.g., "O(n log n) sort on each fetch, O(1) lookup">
      Performance risks: <e.g., "O(n²) nested loop over user list, unbounded input">

Notable Patterns:
  - Caching: <description and files>
  - Recursion: <description, stack depth concern if applicable>
  - Parallelism: <description and mechanism>

Algorithmic Anomalies:
  - <description — e.g., "Linear scan over 10k-record collection inside a UI render cycle">

Computational Profile Summary:
  - <Group>: <dominant profile — e.g., "I/O-bound CRUD" | "CPU-bound graph search" | "memory-bound cache" | "trivial — no significant computation">

Recommended Scope Group Candidates:
  - <Name> — <dominant algorithm or data structure>, <one-line rationale>
```

## Change History
