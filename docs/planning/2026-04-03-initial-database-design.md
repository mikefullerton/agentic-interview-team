# Initial Database Design — Requirements

## Context

The dev-team system uses a DB-centric architecture where all components communicate through the database. This document defines the data types and fields needed as input for schema design.

## Design Rules

See `.claude/rules/db-schema-design.md` for the full set. Key points:
- No blobs or unstructured text — columns must be indexable and searchable
- No computed values (counts, derived booleans) — query the rows
- No unstructured lists — one-to-many data gets its own table
- Separate tables when data is one-to-many or written in a later step by a different actor
- Use join tables for many-to-many relationships between types
- Use project vocabulary for all names

## Types

### Session
A workflow run.
- **playbook**: which workflow definition is being executed
- **team_lead**: which team-lead is running this session
- **user**: who started it
- **machine**: hostname where it was invoked

### Team Member
An actor in the system. Both team-leads and specialists are team members.
- **role**: team-lead or specialist

### Path
A file/repo/project path attached to a session. Flexible — new path types can be added without schema changes.
- **session**: which session this path belongs to
- **path**: the filesystem path or URL
- **type**: what kind of path — repo, project, cookbook, workspace, working_directory

### Session State
An append-only state transition in a workflow. Current status of any actor = their latest row.
- **session**: which session
- **changed_by**: which team member made this transition
- **state**: pending, running, completed, failed, escalated
- **description**: why this transition happened or what's being done

### Retry
A retry of a failed step. One row per retry with the reason.
- **session**: which session
- **session_state**: which state transition triggered the retry
- **reason**: why it was retried

### Result
One specialist's output for a session. Parent of findings.
- **session**: which session
- **specialist**: which specialist produced this result

### Finding
An individual issue within a result. Many findings per result.
- **result**: which result this belongs to
- **session**: which session
- **specialist**: which specialist found it
- **category**: type of finding (gap, recommendation, concern)
- **severity**: critical, major, minor
- **title**: short description of the issue
- **detail**: specific, actionable detail

### Interpretation
Persona translation of a finding. Written in a later step by a different actor (the specialist-persona). Not every finding gets one.
- **finding**: which finding is being interpreted
- **session**: which session
- **specialist**: which specialist's persona wrote this
- **interpretation**: the persona-voiced explanation

### Artifact
A cookbook artifact referenced by findings or state transitions. Linked via join tables (many-to-many).
- **session**: which session
- **artifact**: url or path to the cookbook artifact
- **message**: what the specialist says about it (voice of the actor)
- **description**: expository info about what happened (metadata)

### Message
Team-lead to user interaction. Five types with type-specific attributes.
- **session**: which session
- **type**: question, answer, gate, verdict, notification
- **changed_by**: who sent this message
- **specialist**: which specialist this relates to (if any)
- **content**: the message text
- **category**: for gates (flow, error, conflict) and notifications (progress, result, briefing)
- **severity**: for notifications (info, warning, error)

### Gate Option
A choice within a gate message. One-to-many from message.
- **message**: which gate message this option belongs to
- **option_text**: the choice text
- **is_default**: whether this is the pre-selected option
- **sort_order**: display order

### Reference
A cookbook source consulted by a specialist during analysis. Links a result to a path.
- **result**: which specialist result
- **path**: which cookbook source was consulted
- **type**: guideline, principle, compliance-check

### Playbook
Static definition of a workflow. Declares what must happen and what must be verified.
- **name**: identifier (e.g., interview, generate, lint)
- **team_lead**: which team-lead runs this
- **description**: what this workflow does

### Playbook Phase
A step in a playbook.
- **playbook**: which playbook
- **name**: phase identifier
- **description**: what this phase does
- **order**: sequence

### Playbook Expectation
What must be true for a phase to be considered complete. The playbook declares what, not how — the system is responsible for proving it.
- **playbook_phase**: which phase
- **expectation**: what must be true (e.g., "output is a valid agentic-cookbook-project", "all specialist findings are addressed")

### Playbook Specialist
Specialist assignment to a phase.
- **playbook_phase**: which phase
- **specialist**: which specialist
- **required**: whether this specialist must run or can be skipped

## Relationships

- Finding ↔ Artifact (many-to-many)
- Session State ↔ Artifact (many-to-many)
- Result ↔ Path (many-to-many, via Reference)

## Not a Stored Type

- **Report**: not a table — it's query patterns against the existing data given a session_id. Supports progressive disclosure (overview → specialists → findings → process trace). Designed for LLM consumption with as much data as available.

## Naming Convention: message vs description

These are distinct column types that may appear as separate columns on the same table:

- **message**: a communication from an actor in the system. Messages are translated by the actor's persona. This is the actor speaking.
- **description**: expository information geared toward LLM consumption. Not persona-voiced — just factual context about what happened or what something is.
