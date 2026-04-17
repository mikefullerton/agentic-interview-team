# Team-Lead File Specification

Version: 1.0.0

Team-lead definitions describe the persona and behavior of a workflow orchestrator. They are referenced by workflow files to establish how the team-lead communicates and operates.

## File Location

`team-leads/<name>.md` where `<name>` is lowercase kebab-case.

## Required Sections

Sections MUST appear in this order.

### 1. Title

```markdown
# <Name> Team-Lead
```

- Exactly one `#` heading
- MUST end with ` Team-Lead`
- `<Name>` is the human-readable team-lead name (title case)

### 2. Role

```markdown
## Role
<prose>
```

- 1-3 sentences defining what kind of workflow this team-lead runs
- MUST be non-empty

### 3. Persona

```markdown
## Persona

### Archetype
<1 sentence — what kind of leader this is>

### Voice
<communication style — tone, register, rhythm>

### Priorities
<what this team-lead optimizes for when trade-offs arise>
```

**Sub-sections:**

| Sub-section | Required | Description |
|-------------|----------|-------------|
| Archetype | YES | One sentence defining the leader's identity |
| Voice | YES | Communication style. 2-4 sentences. |
| Priorities | YES | What this team-lead optimizes for. 2-4 sentences. |

### 4. Phases

```markdown
## Phases
- <phase-name> — <description>
```

- Markdown list of phases this team-lead progresses through
- Each entry: `<name> — <description>`
- At least two phases required

### 5. Interaction Style

```markdown
## Interaction Style
<prose or list describing how this team-lead communicates with the user>
```

- How the team-lead uses questions, gates, and notifications
- Whether it talks to the user directly or through other mechanisms

## Validation Rules

| ID | Rule | Severity |
|----|------|----------|
| TL01 | Title matches `# <Name> Team-Lead` pattern | FAIL |
| TL02 | All required sections present in order: Role, Persona, Phases, Interaction Style | FAIL |
| TL03 | Role section is non-empty | FAIL |
| TL04 | Persona has required sub-sections (Archetype, Voice, Priorities) | FAIL |
| TL05 | Phases list has at least two entries | FAIL |
| TL06 | Interaction Style section is non-empty | FAIL |
