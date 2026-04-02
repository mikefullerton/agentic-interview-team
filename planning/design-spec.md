# My Agentic Dev Team — Design Spec

**Date:** 2026-04-01
**Status:** Initial buildout complete. Ready for first test run.

## Overview

A multi-agent interview system that helps users scope and define products they want to build. The system conducts structured, curiosity-driven interviews and produces a folder of markdown transcripts and analyses that an LLM consumes when planning and implementing the build.

## Three-Repo Architecture

1. **agentic-cookbook** — principles, guidelines, recipes. Curated, versioned, stable. Specialists draw initial knowledge from here. Cloned locally as a peer repo.
2. **dev-team** (this repo) — the interviewer system itself. Skill definitions, agent definitions, specialist roster, shared learnings that improve for everyone.
3. **User's interview repo** (e.g., `~/projects/personal/my-agentic-interviews`) — per-user growth. User profiles, transcripts, analyses, per-user specialist maturation, user-specific knowledge base.

## Skill vs. Agent

This is a **skill** (invoked via `/interview` or similar), not a standalone agent. Rationale:
- The interview is inherently interactive and multi-turn
- Skills run in the main conversation context with unlimited back-and-forth
- An agent subprocess would hit `maxTurns` limits
- The skill spawns subagents internally for specialist work

## The Team (Multi-Agent Architecture)

### Roles

| Role | Responsibility | Communication |
|------|---------------|---------------|
| **Meeting leader** | Air traffic controller. Runs the conversation, talks to the user, tells all other team members when to act. Does NOT rephrase specialist questions — passes them through verbatim with attribution. | Direct with user |
| **Transcript analyzer** | Reads the transcript, determines which specialists to bring in, identifies gaps. Acts when the meeting leader tells it to. | Reports to meeting leader |
| **Specialist interviewers** | Ask domain/platform-specific questions. Two modes: structured (known questions) and exploratory (follow threads). Ship with curated starter question sets. | Spawned by meeting leader |
| **Specialist analysts** | Paired with each interviewer. Analyze answers with deep domain expertise. Surface new questions, catch contradictions, identify gaps. Write analysis files. | Run after each answer, report to meeting leader |

### Communication Model

- **Hub and spoke** — meeting leader orchestrates, specialists are subagents that come and go
- **Shared files** — transcript and analysis files serve as persistent shared state any agent can read
- Uses Claude Code's Agent tool as designed

### Question Attribution

The meeting leader passes specialist questions through verbatim:
```
Biff (iOS specialist) asks "Are you using Settings.bundle for system settings or an in-app settings screen?"
```

## Two Dimensions of Specialists

### Domain Specialists
Know their topic across all platforms:
- Security
- Accessibility
- UI/UX & Design
- Software Architecture
- Code Quality & Maintainability
- Testing & QA
- Networking & API
- DevOps & Observability
- Localization & I18n
- Reliability & Error Handling
- Development Process & Product
- Data & Persistence

### Platform Specialists
Know their platform across all domains:
- iOS / macOS / watchOS / tvOS / visionOS
- Android
- Windows
- Web Frontend
- Web Backend / Services
- Database

### Intersection
Power is in the intersection — questions emerge when domain knowledge meets platform knowledge. The meeting leader brings in both dimensions as needed.

### Granularity
Start coarse. Let specialists split as knowledge accumulates (e.g., "security specialist" may eventually become "authentication specialist" + "data privacy specialist" + "network security specialist").

### Specialist Personas
Each specialist gets a named persona (e.g., "Biff, the iOS UI specialist has joined the meeting"). V1 uses generic labels; named personas added later. System designed to support personas from the start.

### Specialist Learning
- Initial knowledge drawn from the agentic-cookbook (principles, guidelines, compliance checks)
- Each specialist ships with a researched, curated starter question set
- Per-user specialist maturation lives in the user's interview repo
- Shared learnings (for everyone) live in this repo
- Migration path from per-user to global maturation later (criteria TBD)

## Interview Flow

### Session Start

1. Infer project from cwd: "I see you're in xyz project, do you want to work on it?"
2. New project → create project directory in interview repo, kick off big-picture discovery
3. Existing project with transcripts → resume mode: "Last time we covered X, Y, Z — what do you want to dig into today?"
4. First time ever → big picture: "What do you want to build? Tell me about yourself. What's the philosophy? What problem is this solving?"
5. Returning user → personalized greeting: "Hey Mike, welcome back." Profile context surfaces only when relevant ("I know you have a lot of iOS experience so I'll factor that in")

### The Interview Loop

```
structured phase (cover known questions via checklist)
    -> explore phase (specialists follow threads, probe implications)
        -> new known things discovered -> back to structured
            -> explore again -> repeat
                -> user says "that's enough" or asks for summary
```

- User can jump straight to explore on a specific topic
- User can say "let's explore X" to kick off the loop starting at explore
- User can come back later and add to the interview ("let's design the Preferences window")

### Living Checklist

- The interview maintains a checklist of what's been covered and what hasn't
- Checklist grows as the interview uncovers new areas
- On resume: "Here's where we are. Covered: vision, document model, toolbar. Still open: preferences window, sharing workflow, export pipeline."

### Per-Exchange Flow

```
meeting leader picks topic
    -> specialist interviewer asks question
        -> user answers
            -> specialist analyst produces deep analysis
                -> analysis surfaces new questions?
                    -> feed back to meeting leader
                        -> next question
```

### Session End

- User asks for a summary
- If summary is good, interview ends (for now)
- User can always come back and continue
- No automatic handoff to planning — a separate skill handles that

## Output Format

### File Naming

Timestamp to the second plus human-readable slug:
```
2026-04-01-19-30-45-preferences-window.md
```
- Guaranteed uniqueness and ordering
- Scannability without opening files
- No collision if two interviews run in parallel

### Two Files Per Exchange

- **Transcript file** — raw Q&A, fully preserved
- **Analysis file** — deep analysis: implications, gaps, contradictions, new questions
- Analysis runs during the interview (not post-mortem) so it can inform the next question

### Frontmatter

Derived from cookbook conventions, trimmed for interview content:

```yaml
---
id: <uuid>
title: <human readable title>
type: transcript | analysis | checklist | profile | summary
created: YYYY-MM-DDTHH:MM:SS
modified: YYYY-MM-DDTHH:MM:SS
author: <user name | meeting leader | specialist name>
summary: <one-line description>
tags: []
platforms: []
related: []
project: <project name>
session: <session identifier>
specialist: <specialist who drove this exchange>
---
```

## Multi-User Support

Designed for multi-user from day one:
- Profiles directory: `profiles/<username>/`
- Each user has own `~/.agentic-interviewer/config.json` with `user_name` field
- Transcript files tagged with `author` in frontmatter
- Checklist shared per-project — all users see what's been covered
- Meeting leader can reference other users' insights
- Specialist maturation is per-user
- Knowledge base is per-repo (shared across users)

## User's Interview Repo Structure

```
my-agentic-interviews/
  profiles/
    mike/
      resume/
      profile.md
    jane/
      resume/
      profile.md
  projects/
    my-ios-app/
      transcript/
      analysis/
      checklist.md
    my-web-service/
      transcript/
      analysis/
      checklist.md
  knowledge/
```

## Four-Repo Architecture (Updated)

| Repo | Path | Purpose |
|------|------|---------|
| agentic-cookbook | `~/projects/agentic-cookbook/agentic-cookbook` | Upstream knowledge |
| dev-team | `~/projects/agentic-cookbook/dev-team` | The system, test harness, personas |
| my-agentic-interviews | `~/projects/personal/my-agentic-interviews` | User's real interview data |
| dev-team-tests | `~/projects/agentic-cookbook/dev-team-tests` | Test output destination |

## Interview Team Repo Structure (Current)

```
dev-team/
  .claude/
    CLAUDE.md                          # Project instructions
    rules/always-commit-and-push.md
    skills/interview -> ../../skills/interview  (symlink, gitignored)
    agents/ -> ../../agents/*          (symlinks, gitignored)
  agents/
    transcript-analyzer.md             # Recommends specialists, identifies gaps
    specialist-interviewer.md          # Generates domain-specific questions (parameterized)
    specialist-analyst.md              # Deep analysis of answers (parameterized)
    simulated-user.md                  # Test-only: plays the role of a user
  skills/
    interview/
      SKILL.md                         # The meeting leader — main entry point
      templates/
        checklist.md                   # Template for new project checklists
        new-project-setup.md           # Project directory setup guide
  rules/
  research/
    specialists/                       # 18 specialist question sets (12 domain + 6 platform)
    cookbook-specialist-mapping.md
    agent-patterns.md
    conversational-patterns.md
  planning/
    design-spec.md                     # This file
    build-history.md                   # Session-by-session build log
  tests/
    personas/                          # 3 test personas (Sarah, Marcus, Priya)
    test-design.md                     # What we test and why
    harness/
      lib/runner.ts                    # Invokes interview via claude -p
      lib/assertions.ts                # Filesystem + interview assertions
      lib/fixtures.ts                  # Fake project creation, test output cleanup
      specs/smoke.test.ts
      specs/persistence.test.ts
      specs/specialist-coverage.test.ts
      specs/resume.test.ts
      vitest.config.ts
      package.json
      tsconfig.json
    fixtures/fake-project/
```

Top-level directories (not `.claude/`) so content is surfaceable for global install.

## Repo Access

- Interviewer has opt-in read access to authorized project repos
- Can notice code changes between sessions
- Config tracks authorized repos
- System detects new repos and asks for permission

## Config (`~/.agentic-interviewer/config.json`)

```json
{
  "interview_repo": "~/projects/personal/my-agentic-interviews",
  "cookbook_repo": "~/projects/agentic-cookbook/agentic-cookbook",
  "interview_team_repo": "~/projects/agentic-cookbook/dev-team",
  "user_name": "mike",
  "authorized_repos": []
}
```

Skill supports `--config <path>` to override the default config location (used by tests).

## Runtime

- Runs locally in Claude Code sessions
- No token optimization in v1 — deep analysis on every exchange, optimize later
- Cookbook repo cloned locally as a peer, referenced by path in config

## Design Philosophy

- "If we build the system right, this will evolve on its own because we designed it correctly"
- Knowledge is categorized and quantified
- Specialists evolve per category as knowledge accumulates
- The container matters more than the initial content
- Each team member has one job
- Start coarse, let things split naturally as they grow

## Key Design Principles

1. **Aggressive persistence** — write transcript immediately on answer, analysis immediately on return, checklist on every topic change. Never buffer.
2. **Each team member has one job** — meeting leader orchestrates, transcript analyzer analyzes coverage, specialist interviewers ask, specialist analysts analyze.
3. **Cookbook access for all agents** — every agent gets cookbook_repo, interview_team_repo, and interview_repo paths. Can read actual guidelines, not just static question sets.
4. **Test flow, not content** — automated tests verify mechanics (files written, specialists invoked, checklist updated), not question quality (which evolves).
5. **Start coarse, split naturally** — specialists begin as broad domains, split as knowledge accumulates.

## Test Mode

Skill supports `--test-mode --persona <path> --max-exchanges <n>`:
- Uses simulated-user agent instead of real user interaction
- Writes flow log (`test-log.jsonl`) for verification
- Bounded execution, no profile updates, config must pre-exist

## Future / Deferred

- Named specialist personas (Biff, etc.)
- Cloud database for persistent layers
- Social media platform integration (cross-pollination with social media management bot team)
- Separate planning skill that reads transcripts and forms a plan
- Global specialist maturation (migration from per-user, criteria TBD)
- Token/cost optimization
- Global install skill
- Interruption recovery test (kill mid-interview, verify persistence)
