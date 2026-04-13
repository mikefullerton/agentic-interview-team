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

## Landscape — other tools doing codebase analysis

### GitNexus
https://github.com/abhigyanpatwari/GitNexus

Zero-server — runs entirely in the browser. Drop in a GitHub repo or ZIP, get an interactive knowledge graph with a built-in Graph RAG agent. No code leaves your machine. The key architectural choice: it precomputes structure at index time (clustering, call tracing, scoring) so AI agent queries return complete context in one call rather than requiring multi-hop lookups. Exposes as an MCP server. Hit #1 on GitHub trending April 2026.

### CodePrism
https://github.com/rustic-ai/codeprism

100% AI-generated codebase (every line of code, test, and config written by AI agents). Does semantic pattern detection rather than syntactic: identifies framework patterns (Flask, Django, FastAPI), data access patterns (Repository, Active Record), security patterns — based on what the code means, not just its structure. Rust-powered, exposes 23 MCP tools.

### Emerge
https://github.com/glato/emerge

Older tool, good technique. Applies Louvain community detection (predecessor to Leiden) combined with TF-IDF semantic search on source files. Does fan-in/fan-out analysis and generates heatmaps based on combined SLOC + fan-out scores — visually identifies files that are both large and heavily depended on. Browser-based D3 visualization.

### Drift
https://github.com/marketplace/actions/drift-architectural-erosion-check

Entirely different angle. Detects architectural erosion specifically from AI-generated code. Uses 23 deterministic signals (no LLM) to find: error handling fragmented across multiple patterns, layer boundary violations, pattern fragmentation. 97.3% precision claimed. Runs as a GitHub Action.

The insight is the opposite of graphify: instead of "help me understand this codebase," it's "alert me when AI coding assistants are degrading the architecture."

### analysis-tools-dev/static-analysis
https://github.com/analysis-tools-dev/static-analysis

Not a tool — a curated directory of hundreds of static analysis tools organized by language. Useful reference.

### Common patterns across the space

Most tools converge on: tree-sitter AST → graph → community detection → LLM or Graph RAG on top. Differentiation is in where it runs (browser, MCP server, local skill), what it detects (structural vs. semantic patterns; erosion vs. comprehension), and whether it uses LLMs.

## Cross-project meta-graph — proposed approach

### The problem

Each project has its own graphify graph — an island. When an LLM helps plan across projects, it either reads a curated overview (shallow) or gets manual context. It has no structural understanding of how projects relate.

### What a cross-project graph gives you

**Commonality detection.** Take god nodes from each project's graph, merge into one graph, run Leiden. Communities that form across project boundaries are shared abstractions. Three projects might all have an "arbitrator" pattern or a "storage provider" pattern — the graph surfaces it without manual inspection.

**Dependency mapping.** Edges between projects reveal coupling. If project A's `SharedDB` god node is referenced by project B's `StorageProvider`, that's a real dependency. Change one, the other breaks.

**Planning leverage.** God nodes in a cross-project graph are the highest-leverage work items — a change there ripples across the most projects. An LLM can say: "these 5 projects share a common auth pattern; fixing it once is 5x the value."

### Architecture

```
graphify (per project)          already have this
        │
        ▼
   graph.json × N projects      existing output
        │
        ▼
   meta-graph builder            ~200 lines of Python
        │
        ▼
   meta-graph.json + report      cross-project structural map
        │
        ▼
   LLM reads at session start    like GRAPH_REPORT.md but portfolio-wide
```

### The meta-graph builder

A Python script that:
1. Walks `~/projects/active/*/graphify-out/graph.json`
2. Extracts god nodes (top N by edge count) with their edges from each project
3. Matches nodes across projects — same name, same import target, or LLM-judged semantic similarity
4. Builds a single NetworkX graph where each node carries a `project` attribute
5. Runs Leiden on the merged graph
6. Outputs `meta-graph.json` and `META_REPORT.md`

### Key design choice: god nodes only

The naive approach — merge all graphs — produces noise. 4,000 nodes per project × 10 projects = 40,000 nodes, useless. The meta-graph uses god nodes only: each project contributes its top 10-20 most-connected abstractions. ~200 nodes total. Communities that form at this level tell you which projects cluster together and why.

### META_REPORT.md contents

- Cross-project communities (which projects cluster and why)
- Shared god nodes (abstractions appearing in multiple projects)
- Cross-project bridges (coupling points between projects)
- Orphan projects (no edges to anything else — fully independent)

### Planning annotations

A lightweight YAML or SQLite layer mapping god nodes to status, priority, blockers. The builder reads these and includes them in the report:

```
Arbitrator (agenticdevteam) — 50 edges, bridges 3 communities
  Status: active development
  Blocks: conductor migration, storage refactor
  Shared with: projectteam (similar pattern)
```

### Where it lives

`~/projects/active/my-projects-overview/` — already indexes all projects. Add:

```
my-projects-overview/
├── meta-graph/
│   ├── build.py              the builder script
│   ├── meta-graph.json       output
│   └── META_REPORT.md        output — the thing LLMs read
├── annotations/
│   └── planning.yaml         status, priority, blockers per node
└── projects/                 already exists
    └── <name>/overview.md
```

### Build order

1. The builder script — god node extraction + merge + Leiden. Get META_REPORT.md generating. Core value.
2. CLAUDE.md integration — wire it so sessions automatically read the report.
3. Planning annotations — add after the structural map reveals what's worth annotating.

## Integration with the devteam project management team

### Existing architecture

The devteam routes work through: skill router → team-lead → arbitrator → specialists → specialty-teams (worker-verifier pairs). There's already a project-manager specialist with 6 teams: schedule, todos, issues, concerns, dependencies, decisions. Specialists read artifacts (cookbook guidelines, project storage files).

### Three integration points

**1. Data source for existing project-manager teams.** The meta-graph report becomes another artifact the existing teams read. No new specialists needed:

- **Dependencies team** — currently tracks dependencies within one project. The meta-graph gives it cross-project dependencies. "Project A's storage layer is structurally identical to project B's."
- **Concerns team** — cross-project coupling points are concerns. A god node bridging 3 projects is a risk.
- **Schedule team** — shared god nodes mean work can't be fully parallelized. The meta-graph tells the schedule team what's actually independent.

**2. New specialist: portfolio analyst.** Operates on the meta-graph (cross-project view), not single-project data. Specialty-teams:

- **commonalities** — shared patterns across projects, candidates for shared libraries
- **coupling** — cross-project bridges, risk of change propagation
- **prioritization** — ranks work items by structural leverage (how many projects benefit)
- **duplication** — where multiple projects solve the same problem independently

Portfolio analyst output feeds back into the project-manager specialist's todos, concerns, and dependencies.

**3. Scoping/interview phase enrichment.** When a team-lead interviews about a new project, it consults the meta-graph: "this looks structurally similar to community X — you already have patterns for this in projects A and B." The interview phase inherits structural context from existing work.

### Data flow

```
graphify (per project)
        │
        ▼
meta-graph builder (my-projects-overview/)
        │
        ▼
META_REPORT.md (artifact)
        │
        ├──▶ project-manager specialist (dependencies, concerns, schedule teams)
        │         reads meta-graph as additional context for single-project analysis
        │
        └──▶ portfolio-analyst specialist (new)
                  reads meta-graph as primary input for cross-project analysis
                  outputs → project-manager's todos, concerns, dependencies
```

The devteam doesn't need to know how the meta-graph was built. It reads a report, same as every other artifact. Graphify stays external, the builder stays external, and the devteam gets structural intelligence about the whole portfolio through a file it already knows how to read.
