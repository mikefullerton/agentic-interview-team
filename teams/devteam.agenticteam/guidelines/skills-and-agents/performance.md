---

id: 7b3e2f91-a84c-4d6e-b1f5-c9a8d3e6f2b7
title: "Performance: Speed and Token Efficiency"
domain: agentic-cookbook://guidelines/implementing/skills-and-agents/performance
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-02
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Optimize Claude Code extensions for speed and token efficiency through shell scripts, model selection, and progressive disclosure."
platforms: []
tags:
  - performance
  - tokens
  - context-window
  - progressive-disclosure
  - shell-scripts
  - model-selection
depends-on:
  - agentic-cookbook://guidelines/skills-and-agents/authoring-skills-and-rules
related:
  - agentic-cookbook://principles/simplicity
  - agentic-cookbook://principles/yagni
  - agentic-cookbook://principles/separation-of-concerns
  - agentic-cookbook://principles/manage-complexity-through-boundaries
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - skill-authoring
  - performance-optimization
---

# Performance: Speed and Token Efficiency

Use shell scripts instead of model calls for deterministic work, pick the cheapest model that handles the task, and load context progressively rather than all at once.

## Overview

Every token spent is time and money. Every model call that could have been a shell script is wasted latency. Every rule line loaded on every turn that's only needed once per session is compounding waste. This guideline establishes three principles for building Claude Code extensions that are fast and token-efficient.

## 1. Use Shell Scripts for Deterministic Work

If the operation is repeatable and has a known outcome, use a shell script. Shell scripts are faster, cheaper, and deterministic — they produce the same result every time without consuming model tokens.

### When to Use a Script

- File scaffolding (creating directories, copying templates, writing boilerplate)
- Git operations (commits, branch creation, status checks)
- Build and lint commands (compile, format, type-check)
- File manipulation (search-and-replace, moving files, generating indexes)
- Environment setup (installing dependencies, checking prerequisites)
- Metrics collection (counting lines, measuring file sizes, generating reports)

### When the Model Is Still Needed

- Decisions that require judgment or context (what to name something, which approach to take)
- Content generation (writing code, documentation, review comments)
- Analysis that requires understanding (identifying gaps, evaluating tradeoffs)
- Adapting to unexpected situations (error diagnosis, recovery strategies)

### How to Apply

- **In skills**: Extract deterministic steps into shell scripts in the skill's directory. The skill invokes the script via Bash, then uses the model for the steps that need judgment.
- **In hooks**: Hooks are already shell commands — they're the natural home for deterministic automation. Use PreToolUse hooks for validation, PostToolUse hooks for formatting and linting.
- **In agents**: When an agent's task includes deterministic subtasks, have it call shell scripts rather than reasoning through known operations. An agent that runs `wc -l` is faster than one that reads a file and counts lines.

## 2. Model Selection Tradeoffs

When a subtask is simple enough for a smaller model, consider downgrading. But measure — don't assume.

### The Decision Framework

Before selecting a smaller model for a subtask, verify three things:

1. **Token efficiency**: Does the smaller model actually use fewer tokens? Some smaller models compensate for lower capability with more verbose output, more retries, or more tool calls. If the smaller model uses the same or more tokens than the larger model, the downgrade is pure cost with no benefit.

2. **Latency**: Does the smaller model complete the subtask faster? If the smaller model needs multiple attempts or produces output that requires correction, the wall-clock time may be worse.

3. **Correctness**: Can the smaller model do the job reliably? A task that looks simple may have edge cases the smaller model mishandles, requiring human intervention or a retry with the larger model.

### When Downgrading Makes Sense

- Template filling with clear structure and no ambiguity
- Simple extraction from well-formatted input (parsing JSON, reading frontmatter)
- Formatting tasks with explicit rules (markdown cleanup, import sorting)
- Classification with a small, well-defined set of categories

### When to Stay on the Larger Model

- Any task involving reasoning about code behavior or architecture
- Tasks where a wrong answer costs more than the token savings
- Tasks that chain — where the output feeds into another model call and errors compound

### When It's Unclear

Ask the user. Present the tradeoff: "This subtask could run on a smaller model — it's a simple extraction. But if it gets it wrong, we'd retry on the larger model anyway. Want me to try the smaller model or just use the current one?" Do not silently downgrade.

## 3. Progressive Disclosure of Context

Load only what's needed for the current step. This is the single highest-leverage optimization for Claude Code extensions.

### The Cost Model

Files in `.claude/rules/` and CLAUDE.md are injected into the system prompt on **every turn** — every user message, every tool call, every response. In a 50-turn conversation, a 10KB rule file consumes ~500KB of context. This cost is invisible and compounding.

Content loaded via tool calls (reading files, invoking skills) is paid once at the point of use. This makes on-demand loading dramatically cheaper for anything not needed on every turn.

### The Three Tiers

**Tier 1 — Always-on (rules, CLAUDE.md):** One-line directives and pointers. This tier pays per-turn cost, so every byte must earn its place. A rule that says "When authoring skills, invoke `/lint-skill` after every change" costs one line per turn. A rule that inlines the entire lint checklist costs 50 lines per turn for something needed once per session.

Target: rule files SHOULD be under 200 lines / ~8KB. Rules that apply to narrow workflows SHOULD be under 10 lines.

**Tier 2 — On-demand (skills, agent prompts):** Guidelines, checklists, and procedures loaded when the workflow step requires them. A skill pulls in the relevant cookbook guidelines when it reaches the step that needs them — not at startup. An agent receives narrow instructions for its specific task.

**Tier 3 — Deep reference (research, full cookbook):** Read only when investigating a specific question or making a decision that requires background. Never loaded unconditionally.

### Applying Progressive Disclosure

- **Rules**: Rules MUST be kept to the minimum directive. Instead of inlining a 38-item checklist, write a one-line pointer: "Run the checklist in `<path>` before marking complete." The checklist loads once when needed, not on every turn.
- **Skills**: Skills SHOULD structure each step to load its own context. A five-step skill SHOULD NOT front-load all five steps' reference material. Step 3 reads the guidelines it needs when step 3 begins.
- **Agents**: Agents MUST receive narrow, specific instructions for one task. Background context SHOULD NOT be included "in case they need it." If the agent needs additional context, it can read it.
- **CLAUDE.md**: CLAUDE.md SHOULD contain only project identity, directory structure, and workflow pointers. Detailed procedures SHOULD be moved into skills. Enforcement SHOULD be moved into rules.

### Real-World Impact

The agentic-cookbook's own rules went from 381 lines / 17,689 bytes per turn to 10 lines / 358 bytes per turn — a 97% reduction — by applying progressive disclosure. The behavioral constraints were preserved; only the delivery mechanism changed.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-02 | Mike Fullerton | Initial creation combining shell script, model selection, and progressive disclosure principles |
