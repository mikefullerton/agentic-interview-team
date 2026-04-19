# `.agenticteam` Bundle Format

On-disk, self-contained form of a team definition. A sibling to the
markdown-tree shape under `teams/<name>/`; both are accepted by
`services.conductor.team_loader.load_team`.

---

## Layout

```
teams/<name>.agenticteam/
  team.json                           # structured manifest (schema-validated)
  guidelines/<group>/<slug>.md        # artifact files at their declared paths
  compliance/<slug>.md
  principles/<slug>.md
  sources/...                         # team-specific reference roots
```

The bundle is a plain directory. Artifact files live at the exact path a
specialty declared in its frontmatter `artifact:` field — no renaming,
no flattening. A sealer copies each referenced file into the bundle
and leaves the rest of the reference pool behind.

## `team.json` (schema v2)

Every authored markdown section maps to a structured JSON field. No
prose is serialized as a bulk string.

```json
{
  "kind": "agenticteam",
  "schema_version": 2,
  "name": "devteam",
  "description": "...",
  "role": "Full-stack product analysis and development consulting...",
  "team_leads": [
    {
      "name": "analysis",
      "frontmatter": { ... },
      "role": "Dispatch specialists against a target...",
      "persona": {
        "archetype": "Technical program manager...",
        "voice": "Direct and structured...",
        "priorities": "Signal over noise..."
      },
      "phases": [
        { "name": "scan",     "description": "understand the target..." },
        { "name": "dispatch", "description": "run specialists..." }
      ],
      "interaction_style": [
        "Only team member who talks to the user",
        "Presents a summary first, then offers drill-down"
      ]
    }
  ],
  "specialists": [
    {
      "name": "platform-database",
      "frontmatter": { ... },
      "role": "Schema design, migrations, indexing...",
      "persona": { "archetype": "...", "voice": "...", "priorities": "..." },
      "sources": [
        "guidelines/database-design/naming-conventions.md",
        "guidelines/database-design/indexing.md"
      ],
      "exploratory_prompts": [
        "If your data model had to support a feature you haven't thought of yet...",
        "What if you needed to change your primary database technology?"
      ],
      "specialties": [
        {
          "name": "indexing",
          "frontmatter": {
            "name": "indexing",
            "description": "...",
            "artifact": "guidelines/database-design/indexing.md",
            "version": "1.0"
          },
          "worker_focus": "Evaluate B-tree fundamentals...",
          "verify": "EXPLAIN QUERY PLAN uses the proposed indexes...",
          "artifact_kind": "reference_resolved"
        }
      ]
    }
  ],
  "consulting": [ ... same shape as specialists ... ]
}
```

Schema: `plugins/dev-team/schemas/agenticteam.schema.json` (JSON Schema
draft 2020-12). Required top-level keys: `kind`, `schema_version`,
`name`, `specialists`.

### Field provenance

| JSON field                          | markdown source                                      |
| ----------------------------------- | ---------------------------------------------------- |
| team `role`                         | `team.md` → `## Role`                                |
| team-lead `role`                    | `team-leads/<lead>.md` → `## Role`                   |
| team-lead `persona.{archetype,voice,priorities}` | `## Persona` → `### Archetype` / `### Voice` / `### Priorities` |
| team-lead `phases[]`                | `## Phases` — bullets of `name — description`        |
| team-lead `interaction_style[]`     | `## Interaction Style` — bulleted list               |
| specialist `role`                   | `specialists/<sp>/specialist.md` → `## Role`         |
| specialist `persona`                | same structure as team-lead persona                  |
| specialist `sources[]`              | `## Cookbook Sources` or `## Sources` — bullet list  |
| specialist `exploratory_prompts[]`  | `## Exploratory Prompts` — numbered list             |
| specialty `worker_focus`            | specialty file → `## Worker Focus`                   |
| specialty `verify`                  | specialty file → `## Verify`                         |

### v1 → v2 changes

- `schema_version: 2`.
- Added structured fields: `role`, `persona`, `phases`, `interaction_style`, `sources`, `exploratory_prompts`.
- **Dropped:** `identity` object, top-level `index`, specialist `index` and `description`, specialty `body`, `Manifest` prose sections (implicit from `specialties[]`).
- **Dropped:** `index.md` files inside the bundle — the JSON structure is the index.
- `artifact_kind` values: `reference` → `reference_resolved`; `output_location` folded into `inline`.

### `artifact_kind` values

| value                  | meaning                                                                   |
| ---------------------- | ------------------------------------------------------------------------- |
| `reference_resolved`   | The declared `artifact:` path exists in the bundle (file was copied in).  |
| `reference_unresolved` | The path was declared but the source file wasn't in any reference root.   |
| `inline`               | Specialty has no `artifact:` — its markdown lives only in `team.json`.    |

Unresolved references are not an error. Teams can legitimately declare
aspirational artifacts (e.g. puppynamingteam's `sources/breed/*.md`) that
haven't been written yet.

## Loader sniffer

```python
from services.conductor.team_loader import load_team

manifest = load_team(Path("teams/devteam"))              # markdown tree
manifest = load_team(Path("teams/devteam.agenticteam"))  # bundle — same result
```

`load_team` picks the bundle path if either (a) the given root has a
`.agenticteam` suffix, or (b) `team.json` is present at the root.
Otherwise it walks the markdown tree. In both cases the return value is
a `TeamManifest` — the runtime model is format-agnostic.

## Tooling

| script                                                | direction          |
| ----------------------------------------------------- | ------------------ |
| `plugins/dev-team/scripts/tree_to_agenticteam.py`     | tree → bundle      |
| `plugins/dev-team/scripts/agenticteam_to_tree.py`     | bundle → tree      |

Both round-trip: tree → bundle → tree produces the original content, and
`load_team` returns equal `TeamManifest`s from either shape (guarded by
`testing/unit/tests/agenticteam/test_rollcall_parity.py`).

## Design decisions

**Real files, not inline blobs.** Reference content lives as actual
markdown files inside the bundle at the declared `artifact:` path. The
alternative (embedding strings in `team.json`) made diffs unreadable,
broke editor tooling, and hid provenance. Keep the filesystem structure
the specialties asked for.

**Bundle is a directory, not a zip.** Zip distribution is deferred. A
plain directory is greppable, diffable in code review, and works with
every git tool. When zip distribution lands later, it will be a wrapper
around the same directory layout.

**Sniffer at `load_team`, not a new entry point.** Callers don't need to
know the shape. Adding a second function (`load_team_bundle`) would have
forked call sites across `conductor`, `rollcall`, `atp_cli`, and tests.
One entry point + a two-line sniff keeps the surface flat.

**`TeamManifest` unchanged.** The bundle is an on-disk format, not a
new runtime model. Everything downstream of `load_team` (realizer,
conductor, whats-next) is oblivious to which shape was on disk.

**`RoleRef` carries `definition_text`, not `path`.** Rollcall discovery
used to hand callers a `Path` so they could re-open the markdown.
Bundles have no filesystem path for each role's text — the content came
from `team.json`. Storing the text on the `RoleRef` directly removes
the format leak and is the only field any caller actually used.

**Reference root pool with suffix matching.** The sealer takes a list
of reference directories (e.g. `~/projects/active/agenticcookbook/
{guidelines,compliance,principles}`) and resolves each `artifact:` path
by suffix-matching against them. This lets one `artifact: guidelines/
database-design/indexing.md` declaration work across many teams without
hard-coding the pool location into the team.

**Both shapes coexist during migration.** Live teams ship as both
markdown tree *and* sealed bundle. The tree is authored; the bundle is
generated and committed for distribution. Retiring the tree is a
separate future step (not this PR's job).

## Related

- Schema: `plugins/dev-team/schemas/agenticteam.schema.json`
- Conversion plan: `docs/planning/2026-04-19-agenticteam-conversion.md`
- Loader: `plugins/dev-team/services/conductor/team_loader.py`
- Architecture: `docs/architecture.md`
