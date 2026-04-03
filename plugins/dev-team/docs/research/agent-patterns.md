# Claude Code Agent Architecture Patterns

Patterns extracted from the agentic-cookbook that apply to the interview team's multi-agent system.

## Agent File Structure

Agents live as markdown files with YAML frontmatter:

```yaml
---
name: agent-name
description: "When to use this agent; trigger keywords"
tools: [Bash, Read, Glob, Grep]   # allowlist
# OR: disallowedTools: [Write]    # denylist
model: sonnet                      # optional model override
maxTurns: 10                       # bounded execution
permissionMode: plan               # plan | bypassPermissions | inherit
---

# Agent Name

System prompt / instructions in markdown body.
```

## Tool Access Patterns

| Agent Role | Recommended Tools | Rationale |
|-----------|------------------|-----------|
| Meeting leader (skill) | All (runs in main context) | Needs full user interaction |
| Transcript analyzer | Read, Glob, Grep | Read-only analysis of files |
| Specialist interviewer | Read, Glob, Grep | Reads cookbook + knowledge, returns questions |
| Specialist analyst | Read, Glob, Grep, Write | Reads transcript, writes analysis files |

## Permission Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `plan` | Read-only, no edits | Transcript analyzer, specialist interviewers |
| `bypassPermissions` | No user prompts | NOT recommended for interview system |
| (inherit) | Same as parent | Default for most subagents |

For the interview system: most subagents inherit permissions. The meeting leader (as a skill) runs in the main context with full permissions. Specialist analysts need Write to create analysis files.

## Bounded Execution

Every agent MUST have `maxTurns` set:
- Simple focused tasks (analyze one answer): 5-10 turns
- Complex analysis (cross-reference multiple answers): 10-15 turns
- Extended research (read cookbook, generate question set): 15-20 turns

## Agent Quality Checklist (Key Items)

From `skills/lint-agent/references/agent-checklist.md`:

| Check | Severity | Applies To |
|-------|----------|-----------|
| S04: description field present | FAIL | All agents |
| C01: Single responsibility | WARN | All agents — each has ONE job |
| C04: Error handling covered | WARN | Interviewers (vague answers), analysts (contradictions) |
| B06: No kitchen-sink | FAIL | Don't combine interviewer + analyst |
| A02: Tool access restricted | WARN | Each agent gets only what it needs |
| A06: maxTurns set | WARN | All agents |

## Hub-and-Spoke Communication

```
Meeting Leader (Skill - main context)
    |
    |-- spawns --> Transcript Analyzer (subagent)
    |                  returns: specialist recommendations, gap analysis
    |
    |-- spawns --> Specialist Interviewer (subagent)
    |                  returns: questions to ask user
    |
    |-- spawns --> Specialist Analyst (subagent)
    |                  returns: analysis insights, new questions
    |                  writes: analysis files to interview repo
```

- Subagents return results to the meeting leader
- Subagents cannot talk to each other directly
- Shared files (transcripts, analyses) serve as indirect communication
- Meeting leader synthesizes all inputs and decides next action

## Vague Answer Handling

From authoring guidelines — be deterministic, not subjective:

**Bad:** "If the answer seems vague, ask for clarification"
**Good:** "If the answer is fewer than 3 sentences AND contains fewer than 2 specific examples, ask a follow-up with a concrete example"

Applied to specialist analysts:
- Check answer against expected detail level for the question type
- Flag specific gaps (not "this is vague" but "no mention of error handling for the offline case")
- Suggest specific follow-up questions

## State Management via Files

The filesystem IS the shared state:

```
projects/<name>/
  transcript/    -- raw Q&A files (append-only)
  analysis/      -- analyst output (append-only)
  checklist.md   -- living checklist (updated in place)
```

Any agent can read any file. Only specialist analysts write analysis files. Only the meeting leader updates the checklist. Transcript files are written by the meeting leader after each exchange.

## Sources

- `skills/lint-agent/references/agent-structure-reference.md`
- `skills/lint-agent/references/agent-checklist.md`
- `cookbook/guidelines/skills-and-agents/authoring-skills-and-rules.md`
