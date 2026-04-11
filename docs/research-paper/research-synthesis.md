# Research Synthesis — Agentic Development Team Corpus

**Generated:** 2026-04-11
**Corpus:** `docs/research-paper/research/` (242 markdown files, ~203,267 words, ~1.6 MB)
**Method:** Inventory → 8-cluster partition → parallel subagent summarization → cross-cluster synthesis.

---

## Executive summary

The corpus is a personal research archive documenting a multi-layered "agentic development team" system built on Claude Code. It spans four years of work compressed into roughly six weeks of active authoring (Feb–April 2026), with a sharp architectural inflection on **2026-04-11**: a pivot from *"the team-lead runs inside a Claude Code conversation"* to *"the team-lead is a headless Python conductor that dispatches work through a pluggable dispatcher."* Most of the material either leads up to, describes, or ripples out from this pivot.

The single most important finding for a research paper is that the corpus is **mid-pivot**, not a finished system — the conductor spec is explicitly marked "research / planning — not a spec," earlier docs describe an architecture the author now considers historical, and several central pieces (LocalDispatcher, database backend, filled-in personas, application maps) are deferred rather than built.

Duplication and contradiction are mostly **intentional and informative** (spec/plan pairs, principle → specialty reuse, parallel checklists), with a small number of **genuine conflicts** that a reader needs to know about:

- **Shell vs. Python scripts** — the Cookbook's Performance guideline says "use shell scripts for deterministic work"; the global CLAUDE.md says *"Always use Python for scripts. NEVER write bash/shell scripts."* This is a real contradiction the author should resolve before publication.
- **Team-lead location** — pre-pivot architecture docs and the post-pivot conductor spec describe incompatible runtimes. Every planning document dated before 2026-04-11 now requires an "as-of" caveat.
- **Consulting team obligation** — the consulting-team spec calls them optional; the database-specialist spec says they *must* be implemented before that specialist can deploy. Local fix, but not yet reflected in the spec.
- **"Concoction" → "cookbook" rename** — incomplete. Multiple files still reference the old term.
- **Specialty count** — architecture.md says 230, extraction plan says 229, database specialist design adds ~22 more. No canonical count exists.

The richest raw material is the `agenticdevteam` planning and spec clusters (Clusters D and E, 35K + 47K words); the most reusable IP is the specialist / worker-verifier / consulting-team pattern; the most provocative through-line is the evolution of the cookbook's rule architecture from 381 lines per turn to 10 lines per turn (a 98% reduction cited across four clusters). A narrative arc that uses the conductor pivot as its climax — with the dev-team, cookbook, and ecosystem all framed as prelude — will read as a story rather than a catalog.

---

## 1. Corpus at a glance

| Metric | Value |
| --- | --- |
| Files | 242 |
| Total words | 203,267 |
| Total size | ~1.6 MB |
| Median words per file | ~500 |
| Files under 100 words (stubs / placeholders) | 80 |
| Files over 5,000 words (long-form specs) | 5 |
| Date range (where dated) | 2026-02 → 2026-04-11 |
| Distinct project prefixes | 14 |

**Top-level distribution by project prefix:**

| Prefix | Files | Words | Avg |
| --- | ---: | ---: | ---: |
| cookbook | 79 | 67,975 | 860 |
| agenticdevteam | 57 | 90,496 | 1,587 |
| devteam | 57 | 6,471 | 113 |
| cookbook-tools | 16 | 10,236 | 639 |
| roadmaps | 8 | — | — |
| agent-registry | 5 | — | — |
| persona-creator | 4 | — | — |
| long tail (11 others) | 16 | — | — |

Key observations from the shape alone:

- `cookbook` is the broadest but shallowest cluster (860 words/file) — reference material and principles.
- `agenticdevteam` is the narrowest and deepest (1,587 words/file) — planning and specs.
- `devteam` has as many files as `agenticdevteam` but **one-fourteenth** the words. Those 57 files are almost entirely templated specialty-team fragments (avg 113 words each), not prose.
- 80 files (33%) are under 100 words — these are stubs, INDEX placeholders, or template fragments. The real intellectual mass is concentrated in the ~37 files over 1,500 words.

---

## 2. The eight clusters

I partitioned the 242 files into eight clusters for parallel analysis. The letters (A–H) are used throughout this document as citation keys.

| # | Cluster | Files | Words | One-line summary |
| --- | --- | ---: | ---: | --- |
| **A** | Cookbook principles & skill authoring | 28 | 7,628 | 20 engineering principles + linting checklists (skill/rule/agent) + authoring guidelines |
| **B** | Cookbook Claude integration | 13 | 21,487 | Hooks, MCP, plugins, self-healing loops, memory, persona prompting, permission bugs, rule optimization |
| **C** | Cookbook workflows, recipes, process | 38 | 38,860 | Five sequential workflows (WF-1…WF-5), compliance specs, ingredient/recipe/cookbook hierarchy, PR-review pipeline |
| **D** | `agenticdevteam` planning docs | 18 | 35,252 | Dated plans: shared DB, router consolidation, compare-code, lint migration, test strategy, **conductor architecture (2026-04-11)** |
| **E** | `agenticdevteam` specs & architecture | 20 | 46,953 | Spec-level docs for conductor, consulting teams, database specialist, team-pipeline, observer, crash recovery, storage-provider — **biggest cluster by words** |
| **F** | Specialists & plugin internals | 76 | 14,762 | 49 specialty-team template fragments + 3 consulting teams + 11 plugin specs + 5 rules + 5 memory anchors — **biggest cluster by file count** |
| **G** | Cookbook-tools skills & rules | 16 | 10,236 | lint-skill / lint-agent / optimize-rules triads, authoring ground rules, permissions rule, committing rule |
| **H** | Long-tail projects & research | 33 | 28,089 | agent-registry, roadmaps, persona-creator, global CLAUDE.md, cat-herding, agentic-auth-service, and 8 smaller / placeholder projects |

**Cluster word density, by decreasing total mass:**

```
E (47K) ────────────────────────────────
C (39K) ──────────────────────────────
D (35K) ──────────────────────────────
H (28K) ─────────────────────────
B (21K) ─────────────────
F (15K) ──────────────
G (10K) ─────────
A  (7K) ──────
```

The "center of gravity" sits squarely in the E+D+C axis — spec, plan, and cookbook process. Everything else is support, tooling, or ecosystem context.

---

## 3. Theme inventory

Eleven meta-themes recur across two or more clusters. These are the conceptual vocabulary of the corpus.

| # | Theme | Clusters it appears in | What it is |
| --- | --- | --- | --- |
| T1 | **Worker–verifier pattern** | D, E, F | A worker produces structured output; an independent verifier checks it; retry up to 3× then escalate. The single most-used pattern in the system. |
| T2 | **Specialty-team template** | D, E, F | YAML frontmatter + `## Worker Focus` + `## Verify`, one file per cookbook artifact. 49 instances in Cluster F. |
| T3 | **Conductor architecture** | D, E, F | A long-running Python process per session, dispatching LLM work through a pluggable dispatcher. Declared 2026-04-11. |
| T4 | **Rule optimization / context efficiency** | A, B, C, F, H | Context injected every turn is expensive; keep rules under 200 lines; push deterministic work to scripts; prefer inline execution to parallel subagents. |
| T5 | **Atomic git workflow (worktree → draft PR → commits → merge)** | C, G, H | Every change flows through a worktree, a draft PR opens on first push, commits are atomic, push immediately. |
| T6 | **Engineering principles (YAGNI, simplicity, separation-of-concerns, design-for-deletion, composition-over-inheritance)** | A, F, H | 20 principles authored in Cluster A are referenced by specialty files in F and global rules in H. |
| T7 | **Cookbook artifact hierarchy (ingredient → recipe → cookbook)** | C, F, G | Three-tier structure replacing earlier flat "recipe" model. Ingredients are atomic, recipes compose them, cookbooks are full assemblies. |
| T8 | **Persona as first-class design primitive** | B, E, H | Personas serve function (traits shape output quality). Same thesis appears in `persona-prompting.md`, `persona-design.md`, and agent-registry/persona-creator. |
| T9 | **Hooks as deterministic automation** | B, C, F, H | Hooks fire at lifecycle points and run scripts; used for verification, yolo-mode, status-line updates, SubagentStop capture. |
| T10 | **Shared database / arbitrator state** | D, E, F | All state flows through one arbitrator backed by SQLite. 21 resource types. Shell-script or Python-script access. |
| T11 | **Hybrid LLM routing / cost control** | E, F, H | $100/mo → $500+/mo cost drift. Strategy: `claude -p` subprocess, logical model names (high-reasoning / fast-cheap / balanced), future LocalDispatcher, token reduction via graphs. |

Three smaller cross-cluster themes worth noting:

- **Skill triadic structure** (A, G) — `SKILL.md` + checklist + structure-reference. A defines it; G implements it.
- **Plugin-vs-install-script dilemma** (B, H) — Recurring open question. Current answer: not a plugin yet.
- **Self-healing loops** (B, D) — Think → act → observe → correct. Cited in rule-optimization pipelines and in the Elasticsearch case study (24 PRs fixed, 20 days saved).

---

## 4. Duplication map

The user explicitly flagged duplication as a priority. The corpus has a lot of it — but most of it is intentional. I've categorized by *type* rather than just listing pairs.

### 4.1 Intentional duplication (keep)

**Spec / plan pairs.** Every major feature has both a design spec (§what and §why) and an implementation plan (§how and §when), almost always co-dated:

| Feature | Spec | Plan |
| --- | --- | --- |
| Consulting team | `agenticdevteam_sp_spec_2026-04-06-consulting-team-design` | `agenticdevteam_sp_plan_2026-04-06-consulting-team` |
| Observer / stenographer | `agenticdevteam_sp_spec_2026-04-06-observer-stenographer-design` | `agenticdevteam_sp_plan_2026-04-06-observer-stenographer` |
| Crash recovery | `agenticdevteam_sp_spec_2026-04-04-crash-recovery-design` | `agenticdevteam_sp_plan_2026-04-04-crash-recovery` |
| Team pipeline | `agenticdevteam_sp_spec_2026-04-08-team-pipeline-design` | `agenticdevteam_sp_plan_2026-04-08-team-pipeline` |
| Compare-code | `agenticdevteam_planning_2026-04-02-compare-code-design` | `agenticdevteam_planning_2026-04-02-compare-code-plan` |
| Shared database | `agenticdevteam_planning_2026-04-02-shared-database-design` | `agenticdevteam_planning_2026-04-02-shared-database-plan` |
| Unified test strategy | `agenticdevteam_planning_unified-test-strategy-design` | `agenticdevteam_planning_unified-test-strategy-plan` |
| Skill test harness | `cookbook_sp_spec_2026-04-04-skill-test-harness-design` | `cookbook_sp_plan_2026-04-04-skill-test-harness` |

**Assessment:** these are the right way to document structured work. Keep all of them. For the research paper, **cite the spec and refer to the plan only when timing / dependencies matter**.

**Specialty-team template replication.** 49 files in Cluster F follow an identical template. Each one covers exactly one cookbook artifact. The "duplication" is structural only — the `Worker Focus` and `Verify` content is unique per file. This is not a duplication problem; it is the system working as designed.

**Parallel checklists (skill, rule, agent).** Cluster A's three lint checklists share identical section scaffolding (Structure & Format / Content Quality / Best Practices) with severity-labeled tables. The "kitchen-sink anti-pattern" and "no CLAUDE.md dump" checks appear in all three. Intentional — and Cluster G's `lint-skill` / `lint-agent` extend the pattern cleanly.

### 4.2 High-value overlap (reconcile at paper-writing time)

**The 98% rule-reduction story.** Cited in four places with slightly different framings:

1. **Cluster A — `cookbook_skills-agents_performance`**: quantified claim ("381 lines / 17,689 bytes per turn to 10 lines / 358 bytes per turn — a 97% reduction").
2. **Cluster B — `cookbook_claude_rule-optimization`**: same numbers, plus the cost model ("in a 50-turn conversation, a 10KB rule file consumes ~500KB of context").
3. **Cluster C — `cookbook_decision_rule-pipeline-architecture` + `cookbook_recipe_claude-rule-optimization-pipeline`**: methodology — `/cookbook-start` + `/cookbook-next` pipeline, generated minimal rules.
4. **Cluster H — global `CLAUDE.md` "Token Efficiency"**: *principle* form of the same idea — "push work into deterministic Python scripts whenever possible."

These are **not in conflict**. They are the same story told at four levels: data point (A), cost model (B), tooling solution (C), personal rule (H). A research paper can thread all four into a single section without editing any source.

**Persona design research across three projects:**

- **Cluster B — `cookbook_claude_persona-prompting`** (systemic rules)
- **Cluster E — `agenticdevteam_research_persona-design`** (dev-team specific)
- **Cluster H — `agent-registry_research_ai-persona-research`**, **`ai-persona-template`**, and **`persona-creator_sp_spec` + `persona-creator_sp_plan`** (platform + generator)

Assessment: these agree on the *thesis* ("traits shape output quality, not just tone"), with different framings. But they have not converged on a single shared artifact — the cookbook's persona guidance is separate from agent-registry's template which is separate from persona-creator's dataclasses. **This is a consolidation opportunity the paper could call out.**

**Worker-verifier pattern definition.** Same definition appears in:

- Cluster D — `agenticdevteam_planning_2026-04-04-ralph-loop-specialist-analysis` (definition + comparison vs. ralph-loop)
- Cluster E — `agenticdevteam_sp_spec_2026-04-11-conductor-design` §4 (as invariant)
- Cluster F — `agenticdevteam_plugin_dev-team_specialist-guide` (operational template)

All three agree. No action needed; the paper should introduce it in Cluster E context and cite the others.

### 4.3 Drift duplication (flag and pick a winner)

**Three overlapping architecture documents:**

| Document | Date | Stance |
| --- | --- | --- |
| `agenticdevteam_architecture` | undated, current | Describes the *present* dev-team system. Uses "specialty-team" terminology. Says 230 teams. |
| `agenticdevteam_planning_2026-04-03-system-architecture-v2` | 2026-04-03 | First DB-centric pass. Team-lead still in Claude Code. **Explicitly superseded.** |
| `agenticdevteam_planning_2026-04-11-conductor-architecture` + `agenticdevteam_sp_spec_2026-04-11-conductor-design` | 2026-04-11 | New target. Team-lead is headless Python. Uses "specialty" terminology (renamed). |

**Winner for the paper:** the conductor docs. `architecture.md` should eventually be rewritten to reflect the conductor model, but it currently documents the old one. The research paper should treat `architecture.md` as "current deployed state, to be replaced" and the conductor spec as "target state."

**Two database planning docs:**

- `agenticdevteam_planning_2026-04-02-shared-database-design` — complete schema + shell-script API
- `agenticdevteam_planning_2026-04-03-initial-database-design` — requirements only, no schema

The -04-02 spec is the newer / more complete document despite having an earlier date in the filename — the -04-03 "initial" doc is requirements-only. Flag for the author to rename or merge.

**Cluster G — two structurally identical skills:** `lint-skill` and `lint-agent` share the same six-step workflow (Version Check → Guards → Resolve Target → Read Target → Fetch Latest Guidance → Review → Report). The only divergences are (a) "all target files" vs. "target" in step 2 and (b) the specific criteria in their checklists. A paper section on linting tools can treat them as a single pattern with one parameter.

### 4.4 Templated / near-empty (tolerable but worth knowing)

- 80 files under 100 words (33% of the corpus). Most are INDEX placeholders, empty project descriptions, or minimal stubs.
- `cookbook_introduction_getting-started` is one sentence long ("TODO: Quickstart guide").
- `agenticdeveloperhub_planning` and `agenticdeveloperhub_project_description` are both "(to be determined)."
- `agentic-kitchen_project_description` and `myagenticworkspace_project_description` are reserved namespaces only.

These are not duplication; they are *absence pretending to be presence*. The paper can either cite them as evidence of ambition that hasn't landed or ignore them.

---

## 5. Conflict map

The user specifically flagged conflicting information as high priority. Here is the full list, ranked by severity.

### 5.1 MAJOR — resolve before publication

**C1. Team-lead runtime location.**

| Source | Claim |
| --- | --- |
| `agenticdevteam_planning_design-spec` (2026-04-01) | "Team-leads run in the user's Claude Code conversation" |
| `agenticdevteam_planning_2026-04-03-system-architecture-v2` | "assumes the team-lead runs in the user's Claude Code conversation" |
| `agenticdevteam_planning_2026-04-02-single-router-skill` | Router loads workflows *inline*; context accumulates in the skill |
| `agenticdevteam_planning_2026-04-11-conductor-architecture` | *"The outer loop is a headless process, not a Claude Code session."* |
| `agenticdevteam_sp_spec_2026-04-11-conductor-design` | Conductor is a long-running Python process; dispatches via `claude -p` |
| `agenticdevteam_memory_project_conductor_pivot` | Confirms pivot; flags all earlier docs as describing the old model |

**Scope:** every architectural planning document dated 2026-04-01 through 2026-04-03 assumes the old model. The conductor pivot reframes them as historical.

**Resolution status:** The pivot doc is explicitly *"research / planning — not a spec,"* so the old model is technically still the active target until the conductor moves into `docs/superpowers/specs/`. No implementation plan exists. The paper should treat the pivot as **declared intent, not shipped state.**

**Recommendation:** the paper should narrate the pivot as the story's climax. Every pre-pivot planning doc becomes *prelude* — the reasoning that led to the conclusion "this cannot run in a Claude Code conversation."

**C2. Shell vs. Python for scripts.**

| Source | Claim |
| --- | --- |
| `cookbook_skills-agents_performance` (Cluster A) | *"Use shell scripts for deterministic operations (scaffolding, git ops, build/lint, file manipulation, metrics collection)."* |
| `agenticdevteam_planning_2026-04-02-shared-database-design` (Cluster D) | *"Shell script API: All access via `scripts/db/*.sh`"* — `db-init.sh`, `db-project.sh`, etc. |
| `agenticdevteam_planning_2026-04-02-performance-optimization` (Cluster D) | *"Shell scripts: `load-config.sh`, `version-check.sh`, `assign-specialists.sh`"* |
| `global_CLAUDE.md` (Cluster H) | **"Always use Python for scripts. NEVER write bash/shell scripts (.sh). This includes hooks, utilities, automation, build helpers, and any standalone script."** |
| `agenticdevteam_sp_spec_2026-04-11-conductor-design` (Cluster E) | *"Team-playbooks authored in Python with 'declarations not programs' convention."* |

**This is a genuine contradiction.** The Cookbook's Performance guideline treats shell as the canonical example of deterministic work; the global CLAUDE.md forbids shell outright for the author's own projects. The planning docs split the difference (shell for DB ops, Python for conductor).

**Resolution status:** Unresolved in the corpus. The author needs to pick one:

1. **Python everywhere** (current global rule) — rewrite the Cookbook Performance guideline and the DB shell-script API.
2. **Shell for deterministic plumbing, Python for logic** (current planning reality) — relax the global rule.
3. **Shell for shipped tooling, Python for personal scripts** — an untested distinction.

**Recommendation:** the research paper should flag this as an open question. If left unresolved, it undermines the cookbook's credibility as a prescriptive guide.

### 5.2 MODERATE — address in a footnote or caveat

**C3. Consulting team obligation.**

- `agenticdevteam_sp_spec_2026-04-06-consulting-team-design`: "Backwards compatible — specialists without consulting teams work exactly as before. The consulting-team section is optional."
- `agenticdevteam_sp_spec_2026-04-06-database-specialist-design`: "Consulting-team support is a new pipeline feature that must be implemented before this specialist can be fully deployed."

Resolution: consulting teams are *optional in general* but *required for specific specialists where decisions cascade*. This is a coherent position; it just hasn't been stated clearly in either spec. **Fix:** add a "Required for" section to the consulting-team spec that names database-specialist as the first obligatory consumer.

**C4. Concoction → cookbook rename, incomplete.**

- `cookbook_sp_spec_2026-04-06-rename-concoction-to-cookbook-design` declares the rename.
- `cookbook_decision_ingredient-recipe-cookbook-hierarchy` v1.1.0 reflects it.
- `cookbook_introduction_glossary` v1.2.0 still uses "concoction."
- Multiple older files still reference "concoction" in prose.

Resolution: in-flight. The rename spec lists 13 files to update but doesn't track completion. **Fix:** run a grep across `docs/research-paper/research/` for "concoction" and either update or explicitly mark remaining files as historical.

**C5. Specialty-team count: 229 vs. 230 vs. ~252.**

- `agenticdevteam_architecture`: "230 teams across 22 categories"
- `agenticdevteam_planning_2026-04-04-specialty-team-extraction-plan`: "Extract 229 specialty-teams from 19 specialist markdown files"
- `agenticdevteam_sp_spec_2026-04-06-database-specialist-design`: proposes 22 new specialty teams (currently 3), implying growth to ~251

Resolution: drift. No canonical count exists. **Fix:** commit to a number, or remove the count from `architecture.md` entirely and cite the directory listing instead.

**C6. Terminology: specialty-team vs. specialty.**

- Conductor spec (Cluster E) explicitly renames `specialty-team → specialty` and `specialty-teams/ → specialties/`.
- Cluster F's specialist-guide still uses "specialty-team."
- The 49 specialty files in Cluster F sit in a directory called `specialty-teams/`.

Resolution: in-flight. Part of the broader 2026-04-11 pivot. Low-impact if the rename is completed; high-impact if left inconsistent because it affects every specialist file's imports.

**C7. Plugin distribution decision (recurring).**

- `cookbook_claude_plugin-format` — cookbook is *not* converting to a plugin; current `clone + /install-cookbook` model is the right fit.
- `cat-herding_research_claude-code-usage-limits` / `roadmaps_research_plugin-vs-install-script` — cat-herding keeps `install.sh` because the Flask dashboard doesn't fit plugin model.
- `dev-tools_research_claude-code-plugins` — covers three loading strategies (`--plugin-dir`, local marketplace, GitHub marketplace) without prescribing.

Not a contradiction — all three independently conclude "not a plugin yet." But the decision is re-derived three times from different angles, and no single document owns it.

### 5.3 MINOR — noteworthy, not blocking

- **C8.** `optimize-rules` skill frontmatter (Cluster G) simultaneously sets `disable-model-invocation: true` and `model: sonnet`. Internal inconsistency in a single file.
- **C9.** `extension-authoring` rule (Cluster G) is explicitly *optional* while every other rule in the same directory is mandatory. Worth a one-line justification in the rule itself.
- **C10.** `dev-team` router version: Cluster D's `single-router-skill` plan bumps to 0.2.0; the `compare-code` plan bumps to 0.4.0. Depending on merge order, the final version is ambiguous.
- **C11.** Cluster D's `unified-test-strategy-plan` references `tests/test-mode-spec.md` as "authoritative" — but that file is itself a Task 1 deliverable in the same plan. Circular reference that resolves once Task 1 ships.
- **C12.** WF-3 REQ-014 ("MUST NOT optimize without evidence") vs. the proactive `rule-optimization-pipeline`. Resolved by scope — one is about application code, the other about shared tooling — but the distinction is never stated.

---

## 6. Gap analysis

Things the corpus repeatedly gestures at but does not deliver. Grouped by kind.

### 6.1 Deferred specs / plans

| Gap | Where referenced | Status |
| --- | --- | --- |
| **Conductor implementation plan** | Conductor spec says a plan will follow in `docs/superpowers/plans/` | Not written |
| **`tests/test-mode-spec.md`** | Unified test strategy plan treats it as canonical | Task 1 deliverable, not yet shipped |
| **LocalDispatcher** | Conductor spec §5.3.2 | Deferred — "concrete open-source target TBD" |
| **Database backend for storage-provider** | Storage-provider spec | "Planned but not part of this spec" |
| **Dashboard rewrite** | Team-pipeline plan | Currently coupled to dev-team SQLite, needs markdown-aware rewrite |
| **Agentic-daemon Phase 2** | Conductor spec | Requires non-Swift job types + Unix socket contract, deferred |
| **Password reset / MFA / rate limiting** | `agentic-auth-service` research | "Open questions / future work" |
| **Roadmaps-v2 (sessions as plan steps)** | Conductor design | Explicitly deferred to a layer above conductor |

### 6.2 Built-but-not-instantiated

Things that have specs and templates but no real instances in the corpus:

- **Application maps.** Formal spec exists in `agenticdevteam_plugin_dev-team_application-map-spec`. No actual maps have been produced.
- **Specialist personas.** Specialist spec defines the `Persona` template (archetype / voice / priorities / anti-patterns). Most specialists have `## Persona: (coming)` placeholders.
- **Test-mode log examples.** `test-mode-spec` defines a unified event schema. No sample `test-log.jsonl` files exist.
- **Filled-in consulting teams.** 3 consulting teams exist, all platform-database-adjacent. No other specialist has adopted the pattern.
- **Live application of the compare-code workflow.** Design and plan both exist; no round-trip case study.

### 6.3 Topics that would strengthen the paper

- **Agent authoring maturity.** Cluster A explicitly states "agent authoring is less mature than skill and rule authoring." Only 5 agent-specific lint criteria vs. 12 skill-specific. No guidance on when to create an agent vs. a skill.
- **Context budgeting holistically.** The rule-optimization work quantifies per-turn rule cost but never budgets the whole context (system prompt + CLAUDE.md + rules + plugin injections + MCP instructions + memory files).
- **MCP server security.** Cluster B catalogs 100+ MCP servers but never discusses sandboxing, read-only modes, audit logs, or deny-lists.
- **Cross-session state between agents.** Memory persists per-session, but how do agents hand off state *between* sessions? Unaddressed.
- **Testing self-healing loops.** Self-healing loops are central to the thesis but no testing strategy exists for them (how do you test that the agent fixed something that was actually broken?).
- **Onboarding.** `cookbook_introduction_getting-started` is a one-line stub. A paper about the cookbook should not leave "how do I start" unanswered.

### 6.4 Empty project slots

- `agenticdeveloperhub` — two placeholder files, no content.
- `agentic-kitchen` — reserved namespace only.
- `myagenticworkspace` — reserved namespace only.
- `name-craft` — project description exists; no planning document.

These can be omitted from the paper entirely, or used as a single-paragraph closing note on the pace of ideation vs. execution.

---

## 7. Suggested narrative arc

The corpus has a natural climax — the 2026-04-11 conductor pivot — and a natural pre-history (cookbook → dev-team → pivot). I recommend organizing the paper around this shape:

### Recommended arc: "Evolution of an Agentic Development Team"

**Part I — Foundations** *(sets the problem and the vocabulary)*

1. **Why an agentic development team?** The cost/context/scale problem. Frames the rest. Draws primarily from Cluster E's `claude-cost-optimization` research and Cluster B's self-healing and memory docs. (~1,500 words)
2. **The Cookbook method.** Principles, guidelines, rules, compliance, and the artifact hierarchy (ingredient → recipe → cookbook). Draws from Clusters A, C, and the cookbook-side of G. Central claim: shared vocabulary lets N projects reuse the same discipline. (~2,500 words)
3. **Claude Code as orchestration language.** Hooks, MCP, plugins, persona prompting, rule optimization. Draws from Cluster B. Central claim: Claude Code is not "the editor," it is the *runtime*. (~2,500 words)
4. **Process discipline.** Five sequential workflows (WF-1…WF-5), atomic commits, guideline checklist, bulk-operation verification. Draws from Cluster C. Central claim: agentic systems still need sequenced human-grade process. (~2,000 words)

**Part II — The dev-team system** *(the core IP)*

5. **Specialists and specialty-teams.** The 1:1 specialist→specialty-team→artifact mapping. The 49-file implementation. Draws from Cluster F and Cluster E specs. (~2,000 words)
6. **Worker–verifier and the consulting team.** The pattern everything depends on. Why retries are bounded at 3. Why consulting teams are required for some domains. Draws from Cluster E. (~2,000 words)
7. **Shared state: the arbitrator, the 21 resource types, and the storage-provider split.** Draws from Clusters D and E. (~1,500 words)
8. **Three refactors, one week.** Router consolidation, compare-code workflow, lint migration — and why they all happened the same week. Draws from Cluster D. (~1,500 words)

**Part III — The pivot** *(the climax)*

9. **The context problem.** Why running team-leads inside a Claude Code conversation stops working at scale. Citation: the 2026-04-11 planning doc's motivation section. (~1,000 words)
10. **The conductor.** Headless Python, single arbitrator, pluggable dispatcher, hybrid judgment model (state machine + LLM at specific nodes). Draws from Cluster E's `conductor-design` spec. (~3,000 words)
11. **Team-pipeline extraction.** Reusable machinery without domain coupling. The "name-a-puppy" validation team. (~1,500 words)

**Part IV — Ecosystem & open questions** *(the coda)*

12. **The wider ecosystem.** agent-registry, persona-creator, roadmaps, agentic-auth-service, cat-herding. The shared identity / auth / planning layer around the dev-team. Draws from Cluster H. (~2,000 words)
13. **Tooling and validation.** `lint-skill`, `lint-agent`, `optimize-rules`, the authoring ground rules. Draws from Cluster G. (~1,500 words)
14. **Open questions.** The 12 conflicts from §5 and the gaps from §6. Treat them as research questions, not defects. (~1,500 words)

**Target total: ~26,000 words.** Ambitious but proportional to the corpus (~12% of raw material).

### Why this arc works

- **It has a story.** The conductor pivot is the climax; everything before is preamble, everything after is coda. A reader who finishes Part II is leaning forward going into Part III.
- **It respects chronology where chronology matters.** The three refactors happened the same week for a reason; that week *is* the story.
- **It uses duplication instead of fighting it.** Spec/plan pairs collapse into single chapters. The 98% rule-reduction story threads through Chapters 2, 3, and 4 without contradicting itself.
- **It makes contradictions visible without making them embarrassing.** Shell-vs-Python becomes a research question in Chapter 14 rather than a buried footnote.
- **It has a clear audience.** A reader who cares about "how do I build my own agentic development team" can read Parts II and III and skip the rest.

### Alternative arcs considered

- **Bottom-up (principles → tools → process → system).** Logical but has no climax. Reads like a textbook, not a paper.
- **Topic-first (one chapter per theme).** Accurate but fights the corpus's chronology. The conductor pivot can't be introduced before Cluster F's memory file, which exists because of the pivot.
- **Case-study-first ("here's how I built the dev-team").** Narrow. Loses the cookbook and ecosystem context that makes the dev-team interesting.

---

## 8. Reading path for a writer approaching this corpus fresh

If I were starting from scratch and had to write the paper in two weeks, I'd read the corpus in this order:

**Day 1 — Ground yourself.**

1. `agenticdevteam_architecture` (Cluster E) — current state
2. `agenticdevteam_planning_2026-04-11-conductor-architecture` (Cluster D) — target state
3. `agenticdevteam_sp_spec_2026-04-11-conductor-design` (Cluster E) — target state, spec form
4. `agenticdevteam_memory_project_conductor_pivot` (Cluster F) — why the pivot happened
5. `global_CLAUDE.md` (Cluster H) — the author's personal rules

**Day 2 — The dev-team fundamentals.**

6. `agenticdevteam_plugin_dev-team_specialist-spec` (Cluster F)
7. `agenticdevteam_plugin_dev-team_specialist-guide` (Cluster F)
8. `agenticdevteam_sp_spec_2026-04-06-consulting-team-design` (Cluster E)
9. Any three specialty files from `devteam_specialty_*` — pick one from claude-code, one from decomp, one from sw-arch (Cluster F)
10. `agenticdevteam_planning_2026-04-04-specialty-team-extraction-plan` (Cluster D) — the refactor that made the pattern scalable

**Day 3 — The cookbook method.**

11. `cookbook_workflow_INDEX` + WF-1 through WF-5 (Cluster C)
12. `cookbook_principles_INDEX` (Cluster A)
13. `cookbook_skills-agents_authoring-skills-and-rules` (Cluster A)
14. `cookbook_skills-agents_performance` (Cluster A)
15. `cookbook_decision_rule-pipeline-architecture` (Cluster C) — the 98% story

**Day 4 — Integration with Claude Code.**

16. `cookbook_claude_hooks-patterns` (Cluster B)
17. `cookbook_claude_mcp-servers` (Cluster B)
18. `cookbook_claude_rule-optimization` (Cluster B)
19. `cookbook_claude_self-healing-research-summary` (Cluster B)
20. `cookbook_claude_plugin-format` (Cluster B)

**Day 5 — The ecosystem + the pivot mechanics.**

21. `agent-registry_research_overview` + persona research (Cluster H)
22. `agentic-auth-service_research_shared-auth-service` (Cluster H)
23. `agenticdevteam_sp_spec_2026-04-08-team-pipeline-design` (Cluster E)
24. `agenticdevteam_research_claude-cost-optimization` (Cluster E)
25. `agenticdevteam_sp_spec_2026-04-07-storage-provider-design` (Cluster E)

After these 25 files (roughly 45K words, 22% of the corpus), a writer has enough to draft Parts I–III. The remaining ~158K words are reference material to pull from while writing.

---

## 9. Open questions for the author

Things only Mike can decide that would materially tighten the paper:

1. **Is the conductor pivot *declared* or *approved*?** The paper's tone depends heavily on this. "We moved to a headless conductor model in April 2026" reads very differently from "we are considering moving to a headless conductor model."
2. **Shell or Python?** §5.2 C2. Pick one before publication, or the reader will notice.
3. **What is the canonical specialty count?** §5.2 C5. If you don't know, cite a directory listing dynamically rather than a static number.
4. **Is "cookbook" the final name?** The rename from "concoction" is incomplete (§5.2 C4). If you're going to rename again, now is the time.
5. **Who is the audience?** Three possible readers:
   - **Other researchers** building their own agentic dev practices → lean into the story and the patterns.
   - **Anthropic / Claude Code team** → lean into the gaps (§6) as feature requests.
   - **Future you** → lean into the contradictions (§5) as resolution targets.
   The arc in §7 assumes the first audience. It's adjustable.
6. **Is `persona-creator` actually going to exist?** Three files of spec and plan, zero implementation. Either cut it from the paper or commit to shipping it before publication.
7. **Should `architecture.md` be deleted and replaced?** It documents the pre-pivot system and will be wrong the moment the conductor lands. If you keep it, date it clearly and mark it historical.
8. **Is Cluster H supposed to be part of this paper at all?** Half of those projects are stubs. A tighter paper would focus on cookbook + dev-team + conductor and treat the rest as context.

---

## Appendix A — One-paragraph cluster summaries

**Cluster A (Cookbook principles & skill authoring, 28 files, ~7.6K words).** The most mature and consistent cluster: 20 engineering principles (YAGNI, simplicity, DI, composition-over-inheritance, design-for-deletion, etc.), plus authoring guidelines and parallel lint checklists for skills, rules, and agents. All files share an identical frontmatter schema, all approved by `approve-artifact v1.0.0` on 2026-04-04, all authored by one person. No internal contradictions. The cluster's single admitted gap is that "agent authoring is less mature than skill and rule authoring."

**Cluster B (Cookbook Claude integration, 13 files, ~21.5K words).** Technical infrastructure for extending Claude Code: hooks (25 lifecycle points), MCP servers (100+ cataloged), plugins (official marketplace + custom), self-healing loops, memory tools, rule optimization (the 98% story), terminal status-line constraints, permission-mode bugs with documented workarounds, persona prompting, API integration, skill testing, and plugin format. No internal contradictions. Biggest gap: there is no integrating essay explaining how these layers compose in a real project.

**Cluster C (Cookbook workflows, recipes, process, 38 files, ~38.9K words).** Five sequential workflows (WF-1 branching → WF-2 planning → WF-3 implementation → WF-4 verification → WF-5 review) wrap everything else. Other content: rule-optimization decision records, ingredient/recipe/cookbook hierarchy (replacing flat recipe model), 38-item guideline applicability checklist, compliance specs per artifact type, atomic commits, scope discipline, PR review pipeline recipe, yolo-mode ingredient, skill test harness design. Minor contradictions around the "concoction → cookbook" rename in flight and the "when to optimize" philosophy. One notable stub: `getting-started.md` is one line.

**Cluster D (agenticdevteam planning docs, 18 files, ~35.3K words).** Week-long evolution of dev-team architecture (2026-04-01 through 2026-04-11) with a dramatic pivot on the last day. Earlier docs (April 1–3) describe a multi-agent system running inside Claude Code; the April 11 doc moves orchestration out entirely into a headless Python conductor. Concrete specifications included: router consolidation (six skills → `/dev-team`), shared database (complete schema + shell-script API), compare-code three-layer asymmetric comparison, lint skill migration, unified test strategy. Contradiction is chronological: the conductor pivot supersedes everything earlier in the cluster.

**Cluster E (agenticdevteam specs & architecture, 20 files, ~47K words — largest by word count).** Spec-level documents for the conductor, consulting teams (cross-cutting verification gates), the database specialist (3 → 22 specialty-teams + 3 consulting teams), storage-provider unification (21 resource types), observer/stenographer (SubagentStop hook + JSONL session logs), crash recovery, test coverage expansion, team-pipeline extraction, cost-optimization research ($100/mo → $500+/mo), agent patterns, conversational patterns, persona design. Four internal contradictions noted: consulting-team optional-vs-required, specialty count drift, DB-backend ownership, and specialty-vs-specialty-team naming. Richest cluster for the research paper.

**Cluster F (Specialists & plugin internals, 76 files, ~14.8K words — largest by file count).** 49 specialty-team template fragments following an identical YAML+Worker Focus+Verify pattern, 3 consulting teams (all platform-database), 11 plugin specs and guides (specialist-spec, specialist-guide, application-map-spec, team-pipeline specs, test-mode-spec), 5 rules (commit-and-push, bump-versions, use-project-directories, optimize-subagent-dispatch, db-schema-design), 5 memory files including the one that declares the conductor pivot. Nearly all files fully specified — no stubs. Notable: the corpus documents the *machinery* of specialists without including any *instantiated* specialists with filled-in personas.

**Cluster G (Cookbook-tools skills & rules, 16 files, ~10.2K words).** Three Claude Code skills (`lint-skill`, `lint-agent`, `optimize-rules`) each composed of a SKILL.md + checklist + optional structure-reference triad. Plus 7 rules anchored by `authoring-ground-rules.md` (atomic permissions, skill versioning, skill authoring, extension authoring, committing via worktree, cookbook integration, generated-cookbook template). `lint-skill` and `lint-agent` are structural mirrors — same six-step workflow, only diverging on plural vs. singular target reads. One internal contradiction: `optimize-rules` frontmatter sets both `disable-model-invocation: true` and `model: sonnet`.

**Cluster H (Long-tail projects & research, 33 files, ~28.1K words across 14 prefixes).** The ecosystem surrounding the dev-team: agent-registry (branded AI identity layer, "DNS for agents"), roadmaps (feature planning orchestration with worktrees and agent workers), persona-creator (Python library + Claude skill for generating personas at three tiers), agentic-auth-service (RS256 JWT microservice shared across all projects), global CLAUDE.md (cross-project rules enforcing token efficiency, Python-only scripts, repo hygiene), cat-herding (personal workflow extensions), myagenticprojects (production SaaS reference architecture). Five projects are placeholders: `agenticdeveloperhub`, `agentic-kitchen`, `myagenticworkspace`, `name-craft`, and two subfolders of `persona-creator`.

---

## Appendix B — Top-15 documents for first-time readers

If a reader can only read 15 files from this corpus, these are the 15:

1. `agenticdevteam_sp_spec_2026-04-11-conductor-design` (E) — target architecture
2. `agenticdevteam_planning_2026-04-11-conductor-architecture` (D) — the pivot narrative
3. `agenticdevteam_architecture` (E) — current state (soon to be historical)
4. `agenticdevteam_plugin_dev-team_specialist-guide` (F) — operational pattern
5. `agenticdevteam_sp_spec_2026-04-06-consulting-team-design` (E) — the cross-cutting gate
6. `cookbook_decision_rule-pipeline-architecture` (C) — the 98% story
7. `cookbook_workflow_INDEX` + `code-planning` + `code-implementation` + `code-review` (C) — the five workflows
8. `cookbook_skills-agents_performance` (A) — why rules cost so much
9. `cookbook_claude_hooks-patterns` (B) — deterministic automation
10. `cookbook_claude_mcp-servers` (B) — the tool gateway
11. `cookbook_claude_self-healing-research-summary` (B) — the think/act/observe loop
12. `agenticdevteam_research_claude-cost-optimization` (E) — the cost motivation
13. `agenticdevteam_sp_spec_2026-04-07-storage-provider-design` (E) — the 21 resource types
14. `agent-registry_research_ai-persona-research` (H) — persona as a design primitive
15. `global_CLAUDE.md` (H) — the author's personal rules

Together these total roughly 40K words — about 20% of the corpus but 80% of the material a new reader needs to understand.

---

*End of synthesis.*
