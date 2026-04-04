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

## Join Tables Needed

- Finding ↔ Artifact (many-to-many)
- Session State ↔ Artifact (many-to-many)

## Still To Design

- **Report**: final user-facing output from team-lead to user
- **Playbook**: static workflow definition — which team-lead, which specialists, phases, inputs, outputs

## Open Questions

- **message vs description distinction**: "message" is the voice of the actor (what they say), "description" is expository metadata (what happened). Should this be a formal rule?
- **Violations table**: deferred from specialty_team discussion — may surface as a way to track specific rule violations found by specialists
