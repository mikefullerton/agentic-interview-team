# Graphify — Research Notes

## What is it

Graphify is a Claude Code skill backed by a Python library. It reads a corpus (code, docs, PDFs, images, audio, video) and builds a knowledge graph — nodes are concepts/symbols, edges are relationships between them. The graph is stored as `graphify-out/graph.json` and can be queried in future sessions without re-reading source files.

The core value: a codebase is too large to fit in an LLM context window, but a graph of it is not. Graphify claims 71.5x fewer tokens per query vs. reading raw files.

## How the graph works

Every extraction returns nodes and edges:

```json
{
  "nodes": [{ "id": "AuthMiddleware", "source_file": "middleware/auth.py", "source_location": "L12" }],
  "edges": [{ "source": "UserService", "target": "AuthMiddleware", "relation": "calls", "confidence": "EXTRACTED" }]
}
```

Edges are tagged with a confidence level:
- `EXTRACTED` — explicitly stated in source (import, call, reference)
- `INFERRED` — reasonable deduction (co-occurrence, call-graph second pass)
- `AMBIGUOUS` — uncertain, flagged for human review

The graph is a NetworkX graph internally. All extractions are merged into one unified graph.

## Pipeline

```
detect() → extract() → build_graph() → cluster() → analyze() → report() → export()
```

Each stage is a single-function module. No shared state — stages communicate via plain Python dicts and NetworkX graphs.

## Three extraction passes

1. **AST pass** (deterministic, no LLM) — tree-sitter parses 23 languages and extracts classes, functions, imports, call graphs, and docstrings.
2. **Transcription pass** (local Whisper) — video/audio files are transcribed using a domain-aware prompt derived from the graph's own god nodes. Cached after first run.
3. **LLM subagent pass** (parallel Claude calls) — docs, PDFs, markdown, images, and transcripts are processed in parallel to extract concepts, relationships, and design rationale.

## Leiden community detection

Leiden is a graph clustering algorithm that partitions nodes into communities — groups that are densely connected internally and sparsely connected externally. It optimizes **modularity** (how much better the community structure is vs. a random graph with the same degree distribution).

### How it runs

1. **Local moving** — each node moves to whichever neighboring community increases modularity most. Repeat until no single move helps.
2. **Refinement** — communities are split into sub-communities to escape local optima. This guarantees communities are internally connected (Louvain, the predecessor, could produce disconnected communities).
3. **Aggregation** — each community is collapsed to a single node, forming a smaller graph. Repeat.

Complexity: O(n log n) in practice. Fast on graphs with millions of nodes.

### Key design insight

Leiden is purely topology-based — it only sees edge density, not node meaning. Graphify exploits this: LLM-extracted semantic edges (`semantically_similar_to`, tagged INFERRED) are added to the same graph as structural edges (`calls`, `imports`). Semantic similarity *becomes* topology. Leiden picks it up without a separate embedding step.

This is why graphify has no vector database. The graph structure is the similarity signal.

## What the graph enables

### Impact analysis
- What breaks if I change X? (find all nodes with edges pointing at X)
- Is it safe to delete this file? (check for incoming edges)
- What does this module actually depend on? (traverse outgoing edges)

### Architectural analysis
- Find god classes (nodes with unusually high edge counts)
- Find hidden coupling (nodes that bridge otherwise separate communities)
- Verify intended layering (does the data layer ever call the UI layer?)
- Find circular dependencies (cycles in the graph)

### Dead code / orphan detection
- Nodes with zero incoming edges that aren't entry points are unreachable
- Weakly-connected subgraphs are isolated islands

### Refactoring planning
- Communities with low cohesion should be split
- Communities with many inter-edges are candidates for merging
- Find the natural seam to extract a module (the cut with fewest cross-edges)

### Test coverage gaps
- Map test files to the nodes they exercise
- Nodes with no test-file edges pointing at them are untested
- God nodes with no test coverage = highest risk

## Relevance to the devteam scoping phase

When the devteam investigates a target app, agents currently read files. The graph would replace that with navigation:

- **Team lead** uses god nodes to identify core abstractions immediately, and communities to partition work across specialists
- **Specialist agents** start at a relevant god node and traverse its subgraph — no file reading needed, much lower token cost
- **Recipe generation** maps directly to community structure — recipe sections correspond to architectural boundaries that the graph extracted deterministically
- **Finding seams** (the key scoping question) becomes: find communities with low inter-community edge counts. Graph answers it directly.

The compounding benefit: the graph is shared state. One extraction pass, every agent in the session benefits.

## What's standard vs. non-obvious

**Standard pieces:**
- tree-sitter AST parsing
- NetworkX
- Leiden algorithm
- LLM extraction prompting
- Whisper transcription
- SHA256 file caching

**Non-obvious design choices:**
- No embeddings / no vector DB — semantic similarity lives in the graph as edges, not in a separate vector space
- Confidence tagging at extraction time (not post-hoc)
- Domain-aware Whisper prompts bootstrapped from the graph's own god nodes (the graph improves its own extraction quality)
- Unified graph for both structural and semantic edges — Leiden sees both simultaneously
