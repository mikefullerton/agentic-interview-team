# Specialist Guide

The canonical reference for the specialty-team architecture — how specialists are structured, how specialty-teams work, and how specialists participate in dev-team workflows.

## Architecture

```
Specialist (role + persona)
  └── manages N specialty-teams, one at a time
        └── Specialty-Team (focused on ONE guideline/principle/rule)
              ├── Worker — does the work for this artifact
              ├── Verifier — checks the work, independent of worker
              └── Loop until verifier signs off
```

### Specialty-Team

The atomic unit. A worker-verifier pair that is an absolute expert on ONE cookbook artifact (a single guideline, principle, or rule).

- **Worker** — receives the cookbook artifact, the target (transcript/code/recipe), and the mode. Produces work product. Uses `agents/specialty-team-worker.md`.
- **Verifier** — receives the cookbook artifact and the worker's output. Checks completeness and correctness. Returns PASS or FAIL with specifics. Uses `agents/specialty-team-verifier.md`.
- **Independence** — the worker cannot affect what the verifier checks. The verifier cannot influence what the worker does. This is checks-and-balances.
- **Loop** — if the verifier returns FAIL, the worker gets the failure reasons and retries. Max 3 iterations, then escalate to the specialist with the failure details.

### Specialist

An organizer. A specialist holds a role and persona, manages a list of specialty-teams, and runs them one at a time.

- **Role** — what this specialist covers (e.g., "Auth, transport security, token handling, input validation, secure storage, sensitive data, privacy, dependency security, CORS, CSP, user safety")
- **Persona** — (coming) shapes how the specialist communicates, prioritizes, and aggregates
- **Team manifest** — the list of specialty-teams this specialist manages. Each cookbook artifact the specialist owns = one specialty-team.
- **Iteration** — a deterministic script (`scripts/run-specialty-teams.sh`) parses the manifest and outputs the team list. The orchestrating agent walks the list one at a time.
- **Aggregation** — after all teams complete, the specialist aggregates findings into a unified report
- **Sign-off** — the specialist cannot sign off until every specialty-team's verifier has signed off (or escalated after max iterations)

### Key Principle

The specialty-teams ARE the specialist's skill set. The specialist doesn't "know" security — it manages the specialty-teams for authentication, authorization, token-handling, CORS, CSP, etc. Each team is the real expert. The specialist is the manager.

## Specialist File Format

Every specialist file in `specialists/` follows this structure:

```markdown
# <Name> Specialist

## Role
<1-2 sentences defining scope>

## Persona
(coming)

## Cookbook Sources
<explicit file paths — same as before, used for alignment checking>

## Specialty Teams

### <team-name>
- **Artifact**: `<path to one cookbook artifact>`
- **Worker focus**: <what this team cares about — mode-independent>
- **Verify**: <acceptance criteria — what the verifier checks>

### <next-team>
...
```

### Rules for Specialty Teams

1. **One team per cookbook artifact.** If a specialist owns `guidelines/security/authentication.md`, that's one team named `authentication`.
2. **Worker focus is mode-independent.** It describes what this team cares about, not how it operates. The mode (interview/analysis/generation/review) determines the how.
3. **Verify criteria are concrete.** Not "check auth is good" but "auth method chosen, PKCE for public clients, no implicit flow."
4. **Every artifact gets a team.** If a specialist lists a cookbook source in `## Cookbook Sources`, there must be a corresponding specialty-team. If it's a directory reference (e.g., `guidelines/security/`), every file in that directory gets its own team.

## Modes

The same specialty-team pipeline runs in all four modes. The worker's behavior changes per mode:

| Mode | Worker receives | Worker produces | Verifier checks |
|------|----------------|-----------------|-----------------|
| **interview** | Artifact + transcript | One question + why it matters | Question addresses artifact's core concern; not already answered |
| **analysis** | Artifact + source code | Findings per requirement (present/absent/violation/n-a) | Every requirement has a finding with evidence |
| **generation** | Artifact + generated code + recipe | Code additions/modifications | Code satisfies requirements; compiles; additive only |
| **review** | Artifact + recipe | Coverage status per requirement + suggestions | Every requirement mapped to recipe content or flagged |

## Execution Flow

1. The orchestrating workflow (interview, create-project-from-code, create-code-from-project, generate, lint) determines which specialists to assign
2. For each specialist, the orchestrator runs `scripts/run-specialty-teams.sh <specialist-file>` to get the team manifest as JSON
3. The orchestrator walks the team list one at a time:
   a. Spawn worker agent with: mode, artifact, target, worker focus
   b. Spawn verifier agent with: artifact, worker output, verify criteria
   c. If FAIL and iterations < 3: feed failure back to worker, retry
   d. If PASS: record result
   e. If FAIL after 3: record escalation
4. After all teams complete, the specialist aggregates results
5. Specialist signs off (or reports escalations)

The iteration is deterministic — a script walking a list. The LLM cost is in the worker-verifier calls (small, focused). The specialist doesn't need to hold all teams in context at once.

## Specialist Assignment

Unchanged. The rules in `research/specialist-assignment.md` and `research/specialist-assignment.json` determine which specialists are assigned to a recipe or codebase. The shell script `scripts/assign-specialists.sh` automates this.

## Cross-Domain Responsibilities

Each specialty-team stays focused on its ONE artifact. However, workers are expected to flag critical cross-domain issues they notice:

- A security worker reviewing auth notices no rate limiting — flags it
- A UI worker generating form code notices unsanitized input — flags it

Flags go to the specialist's aggregation report under a "Cross-Domain Flags" section. The specialist does not fix them — the appropriate specialist's teams handle their own domain.

## Adding a New Specialist

1. Create `specialists/<domain>.md` following the format above
2. Define specialty-teams — one per cookbook artifact the specialist owns
3. Add the specialist to `research/cookbook-specialist-mapping.md`
4. Test: run one specialty-team in each mode to verify the worker focus and verify criteria produce good results
5. Run `align-specialists` to confirm coverage maps are clean
