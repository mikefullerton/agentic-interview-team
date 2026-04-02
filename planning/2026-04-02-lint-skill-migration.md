# Migrate Cookbook Lint Skills to Dev-Team Specialist System

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move 7 cookbook lint/review skills into the dev-team plugin as a new `/dev-team-lint` skill backed by the specialist system, rename existing skills to verb-based commands, and document responsibilities.

**Architecture:** The Linter is a fifth dev-team role. It auto-detects artifact type (skill, rule, agent, recipe, implementation), runs structural validation (checklist-based, deterministic), then specialist review (domain-based, judgment-requiring), and produces a unified PASS/WARN/FAIL report. It reuses the existing specialist dispatch pattern (recipe-reviewer agent pattern generalized to an artifact-reviewer).

**Tech Stack:** Markdown skills, markdown agents, shell scripts for deterministic checks, specialist question sets.

---

## Context

The cookbook repo has 7 standalone lint/review skills that each inline their own domain knowledge. The dev-team plugin has a specialist system with 19 specialists, each with cookbook source mappings and three participation modes. The standalone skills duplicate what the specialist system does better — they apply domain expertise to evaluate artifacts against standards. This plan migrates those skills into the dev-team as a unified `/dev-team-lint` skill, removes them from the cookbook, and renames existing dev-team skills to a consistent verb-based pattern.

## Dev-Team Responsibility Map

| Role | Command | Responsibility |
|------|---------|---------------|
| **Interviewer** | `/dev-team-interview` | Discover product requirements through structured and exploratory questioning with specialist expertise |
| **Cookbook Analyzer** | `/dev-team-analyze <target>` | Reverse-engineer an artifact into cookbook format — codebase into cookbook project |
| **Cookbook Project Generator** | `/dev-team-generate <target>` | Improve a cookbook project through specialist review — review recipes, suggest changes, apply approved improvements |
| **Project Builder** | `/dev-team-build <target>` | Build working code from a cookbook project — scaffold, generate, augment with specialists, compile, test |
| **Linter** | `/dev-team-lint <target>` | Evaluate any artifact against cookbook standards — skills, rules, agents, recipes, implementations — produce PASS/WARN/FAIL report with specialist findings |

## Migration Map

| Cookbook Skill (removed) | Dev-Team Equivalent |
|--------------------------|-------------------|
| `/lint-skill` | `/dev-team-lint <skill-path>` |
| `/lint-rule` | `/dev-team-lint <rule-path>` |
| `/lint-agent` | `/dev-team-lint <agent-path>` |
| `/lint-recipe` | `/dev-team-lint <recipe-path>` |
| `/lint-compliance` | `/dev-team-lint <recipe-path> --compliance-only` |
| `/lint-project-with-cookbook` | `/dev-team-lint <impl-dir> --recipe <recipe-path>` |
| `plan-cookbook-recipe` compliance step | Delegates to Linter internally |

## Skills NOT Migrated

- **`optimize-rules`** — File-transformation pipeline (backup, merge, delete, revert). Not a review/evaluation tool. Stays in cookbook.
- **`plan-cookbook-recipe`** — Conversational recipe authoring. Stays in cookbook, but its compliance guidance phase can delegate to the Linter.

---

## Task 1: Promote lint checklists to cookbook guidelines

The three lint checklists currently live as skill reference files. They need to become canonical cookbook guidelines so both the dev-team specialist and any future standalone tools read from one source of truth.

**Files:**
- Copy: `cookbook/skills/lint-skill/references/skill-checklist.md` → `cookbook/cookbook/guidelines/skills-and-agents/skill-checklist.md`
- Copy: `cookbook/skills/lint-rule/references/rule-checklist.md` → `cookbook/cookbook/guidelines/skills-and-agents/rule-checklist.md`
- Copy: `cookbook/skills/lint-agent/references/agent-checklist.md` → `cookbook/cookbook/guidelines/skills-and-agents/agent-checklist.md`
- Copy: `cookbook/skills/lint-skill/references/skill-structure-reference.md` → `cookbook/cookbook/guidelines/skills-and-agents/skill-structure-reference.md`
- Copy: `cookbook/skills/lint-rule/references/rule-structure-reference.md` → `cookbook/cookbook/guidelines/skills-and-agents/rule-structure-reference.md`
- Copy: `cookbook/skills/lint-agent/references/agent-structure-reference.md` → `cookbook/cookbook/guidelines/skills-and-agents/agent-structure-reference.md`
- Modify: `dev-team/research/specialists/claude-code.md` — add these 6 files as cookbook sources

- [ ] **Step 1:** Copy the 6 reference files to `cookbook/cookbook/guidelines/skills-and-agents/`
- [ ] **Step 2:** Add cookbook frontmatter (id, title, domain, type: guideline) to each copied file
- [ ] **Step 3:** Update `dev-team/research/specialists/claude-code.md` Cookbook Sources section to reference the 6 new guideline files
- [ ] **Step 4:** Commit and push both repos

---

## Task 2: Rename existing dev-team skills to verb-based commands

**Files:**
- Rename: `skills/interview/` → `skills/interview/` (already verb — no change needed, just update SKILL.md name field)
- Rename: `skills/analyze-project/` → `skills/analyze/`
- Rename: `skills/generate-project/` → `skills/generate/`
- Rename: `skills/build-project/` → `skills/build/`
- Modify: `.claude-plugin/plugin.json` — update skill references if listed
- Modify: `CLAUDE.md` — update skill command references

- [ ] **Step 1:** Rename `skills/analyze-project/` directory to `skills/analyze/`
- [ ] **Step 2:** Update `skills/analyze/SKILL.md` frontmatter: `name: dev-team-analyze`, update description to mention `<target>` argument
- [ ] **Step 3:** Rename `skills/generate-project/` directory to `skills/generate/`
- [ ] **Step 4:** Update `skills/generate/SKILL.md` frontmatter: `name: dev-team-generate`
- [ ] **Step 5:** Rename `skills/build-project/` directory to `skills/build/`
- [ ] **Step 6:** Update `skills/build/SKILL.md` frontmatter: `name: dev-team-build`
- [ ] **Step 7:** Update `.claude-plugin/plugin.json` if it references old skill names
- [ ] **Step 8:** Update `CLAUDE.md` skill list with new command names and responsibility descriptions
- [ ] **Step 9:** Grep for old skill names across the entire repo (agent files, other skills) and update all references
- [ ] **Step 10:** Commit and push

---

## Task 3: Create the artifact-reviewer agent

This generalizes the existing `recipe-reviewer` agent pattern to handle any artifact type (skill, rule, agent, recipe, implementation). The recipe-reviewer stays as-is for generate-project; this is a new agent for the Linter.

**Files:**
- Create: `agents/artifact-reviewer.md`

- [ ] **Step 1:** Read `agents/recipe-reviewer.md` as the template
- [ ] **Step 2:** Create `agents/artifact-reviewer.md` with:
  - Input: artifact path, artifact type (skill|rule|agent|recipe|implementation), specialist domain, specialist question set path, cookbook sources (including lint checklists), recipe path (for implementation mode)
  - Tools: Read, Glob, Grep (read-only, same as recipe-reviewer)
  - maxTurns: 15
  - Review process: read artifact → read appropriate checklist → read cookbook guidelines → evaluate each check → produce PASS/WARN/FAIL per check → produce suggestions with cookbook references
  - Output format: matches existing lint skill output (structured PASS/WARN/FAIL table + suggestions + summary)
  - Artifact-type-specific behavior:
    - **skill**: use skill-checklist.md (S/C/B series checks)
    - **rule**: use rule-checklist.md (C/B/R/O series checks)
    - **agent**: use agent-checklist.md (S/C/B/A series checks)
    - **recipe**: use recipe template + conventions.md (F/S/R/T/K series checks)
    - **implementation**: use guideline-checklist.md + recipe requirements
- [ ] **Step 3:** Commit and push

---

## Task 4: Create the `/dev-team-lint` skill

**Files:**
- Create: `skills/lint/SKILL.md`

- [ ] **Step 1:** Create `skills/lint/SKILL.md` with frontmatter:
  ```yaml
  name: dev-team-lint
  description: Evaluate skills, rules, agents, recipes, or implementations against cookbook standards. Produces PASS/WARN/FAIL report.
  argument-hint: <path> [--type skill|rule|agent|recipe|implementation] [--recipe <path>] [--compliance-only]
  ```
- [ ] **Step 2:** Implement auto-detection logic in skill body:
  - Directory with `SKILL.md` → skill
  - `.md` file with agent frontmatter (tools, maxTurns) → agent
  - `.md` file with recipe frontmatter (type: recipe) → recipe
  - `.md` file in a rules directory or without special frontmatter → rule
  - Directory with source files + `--recipe` flag → implementation
  - `--type` flag overrides auto-detection
- [ ] **Step 3:** Implement the lint pipeline:
  1. Read config (`~/.agentic-cookbook/dev-team/config.json`) for cookbook_repo path
  2. Auto-detect or accept artifact type
  3. Determine specialist assignment:
     - All Claude Code artifacts → Claude Code specialist (always)
     - Recipes → Claude Code specialist + domain specialists based on recipe content
     - Implementations → same logic as generate-project specialist assignment
  4. Spawn artifact-reviewer agent per specialist (parallel, 2-3 at a time)
  5. Compile results into unified report
  6. Present findings with suggestions
  7. User approval gate for any fix suggestions
  8. Apply approved fixes
  9. Persist report to workspace_repo
- [ ] **Step 4:** Add `--compliance-only` mode: skip structural and domain checks, only run compliance evaluation
- [ ] **Step 5:** Commit and push

---

## Task 5: Add Claude Code specialist augmentation section to specialist-code-pass agent

The specialist-code-pass agent has domain-specific augmentation guides for each specialist. The Claude Code specialist needs one.

**Files:**
- Modify: `agents/specialist-code-pass.md`

- [ ] **Step 1:** Read `agents/specialist-code-pass.md`
- [ ] **Step 2:** Add `### claude-code` section after the platform specialists section:
  ```
  ### claude-code
  **Focus sections:** All (skills, rules, agents are the primary artifacts)
  **What to add:**
  - Progressive disclosure structure (tier 1/2/3 context loading)
  - Shell script extraction for deterministic operations
  - Proper frontmatter fields and validation
  - Context budget annotations (line counts, per-turn cost notes)
  - Skill versioning and version check boilerplate
  - Hook wiring for deterministic automation
  - Permission prompts before file modifications
  ```
- [ ] **Step 3:** Commit and push

---

## Task 6: Update CLAUDE.md and plugin manifest with responsibility map

**Files:**
- Modify: `CLAUDE.md`
- Modify: `.claude-plugin/plugin.json` (if needed)

- [ ] **Step 1:** Read current `CLAUDE.md`
- [ ] **Step 2:** Replace the Skills section with the responsibility map table (Role, Command, Responsibility)
- [ ] **Step 3:** Add the Linter to the skill list
- [ ] **Step 4:** Update any references to old skill names throughout the file
- [ ] **Step 5:** Read `.claude-plugin/plugin.json` and update if it references skills
- [ ] **Step 6:** Commit and push

---

## Task 7: Remove migrated skills from cookbook repo

Only after the dev-team lint skill is working.

**Files (all in cookbook repo):**
- Remove: `cookbook/skills/lint-skill/`
- Remove: `cookbook/skills/lint-rule/`
- Remove: `cookbook/skills/lint-agent/`
- Remove: `cookbook/skills/lint-recipe/`
- Remove: `cookbook/skills/lint-compliance/`
- Remove: `cookbook/skills/lint-project-with-cookbook/`
- Modify: `cookbook/CLAUDE.md` — remove these skills from the skills table
- Modify: `cookbook/README.md` — remove these skills from documentation

- [ ] **Step 1:** Verify `/dev-team-lint` works for each artifact type (manual test)
- [ ] **Step 2:** Remove the 6 skill directories from the cookbook repo
- [ ] **Step 3:** Update cookbook `CLAUDE.md` to remove the skills and note they moved to the dev-team plugin
- [ ] **Step 4:** Update cookbook `README.md` similarly
- [ ] **Step 5:** Commit and push cookbook repo

---

## Task 8: Update plan-cookbook-recipe to delegate compliance to Linter

**Files (cookbook repo):**
- Modify: `cookbook/skills/plan-cookbook-recipe/SKILL.md`

- [ ] **Step 1:** Read `cookbook/skills/plan-cookbook-recipe/SKILL.md`
- [ ] **Step 2:** In the compliance guidance phase, add delegation: if dev-team plugin is available, invoke `/dev-team-lint <recipe> --compliance-only` instead of inline compliance evaluation
- [ ] **Step 3:** Keep the inline compliance logic as fallback for users without dev-team
- [ ] **Step 4:** Commit and push cookbook repo

---

## Verification

1. **Lint a skill:** Run `/dev-team-lint path/to/some/skill/` — should auto-detect as skill, run S/C/B series checks via Claude Code specialist, produce PASS/WARN/FAIL report
2. **Lint a rule:** Run `/dev-team-lint path/to/some/rule.md` — should auto-detect as rule, run C/B/R/O series checks
3. **Lint an agent:** Run `/dev-team-lint path/to/some/agent.md` — should auto-detect as agent, run S/C/B/A series checks
4. **Lint a recipe:** Run `/dev-team-lint path/to/some/recipe.md` — should run structural checks + domain specialist review
5. **Lint an implementation:** Run `/dev-team-lint path/to/impl/ --recipe path/to/recipe.md` — should run guideline + recipe conformance checks
6. **Renamed skills work:** Run `/dev-team-analyze`, `/dev-team-generate`, `/dev-team-build` — verify they invoke correctly
7. **Cookbook skills removed:** Verify `/lint-skill`, `/lint-rule` etc. no longer exist in cookbook
8. **plan-cookbook-recipe delegation:** Run `/plan-cookbook-recipe` and verify compliance phase delegates to dev-team if available
