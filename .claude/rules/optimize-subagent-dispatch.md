---
globs: skills/**,agents/**,planning/**
---

# Optimize Subagent Dispatch

When planning or executing work that involves dispatching subagents, apply these principles:

## Model Selection

- **Mechanical tasks** (transcribing from a plan, copying exact content, simple renames, adding a row to a table): use a fast/cheap model. The plan already has the answer — the agent just writes it.
- **Judgment tasks** (writing workflows, designing orchestration, interpreting ambiguous results, creating new agent instructions): use the full model.
- If unsure, ask: "Does this task require the agent to make decisions, or just follow instructions?" Decisions need the full model. Instructions need the fast model.

## Parallelism

- Identify independent tasks and dispatch them in parallel. Two tasks are independent if neither reads the other's output.
- Group mechanical tasks together for parallel dispatch. Group judgment tasks separately.
- Don't parallelize tasks that write to the same file.

## Review

- Skip two-stage review (spec + quality) for mechanical tasks transcribed from a plan with exact content. The plan IS the spec.
- Review judgment tasks — the workflow files, agent definitions, and anything that required creative decisions.

## Progressive Disclosure

- Don't front-load all context into every agent prompt. Give the agent what it needs for its specific task.
- For mechanical tasks: provide the exact content to write and the file path. Nothing else.
- For judgment tasks: provide the design spec, existing patterns to follow, and constraints.
