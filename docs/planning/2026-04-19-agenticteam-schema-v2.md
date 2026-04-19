# `.agenticteam` Schema v2 — Formalize Section Fields

**Goal:** Stop serializing markdown as strings. Every authored section gets a structured JSON field. Drop `index.md` (JSON structure is the index), drop `body` blobs, drop redundant `Manifest` sections. Same bundle layout, v2 `team.json`.

**Scope:** `team.json` shape + schema + converter + loader + tests + regenerate live bundles. No changes to runtime callers (`TeamManifest` surface stays compatible — add fields, don't rename existing ones).

**Out of scope:** Retiring the authored markdown tree (Phase 5, separate decision).

---

## Schema v2 shape

```json
{
  "kind": "agenticteam",
  "schema_version": 2,
  "name": "devteam",
  "description": "...",                    // optional, from team.md frontmatter
  "role": "...",                            // team.md "## Role" section
  "team_leads": [
    {
      "name": "analysis",
      "frontmatter": { ... },
      "role": "...",
      "persona": {
        "archetype": "...",
        "voice": "...",
        "priorities": "..."
      },
      "phases": [ { "name": "scan", "description": "..." }, ... ],
      "interaction_style": ["...", "..."]
    }
  ],
  "specialists": [
    {
      "name": "platform-database",
      "frontmatter": { ... },
      "role": "...",
      "persona": { "archetype": "...", "voice": "...", "priorities": "..." },
      "sources": ["guidelines/database-design/indexing.md", "..."],
      "exploratory_prompts": ["...", "..."],
      "specialties": [
        {
          "name": "indexing",
          "frontmatter": { ... },
          "worker_focus": "...",
          "verify": "...",
          "artifact_kind": "reference_resolved"
        }
      ]
    }
  ],
  "consulting": [ ... same shape as specialists, minus specialties ... ]
}
```

**Dropped vs v1:** `identity` object, `index` objects, specialty `body`, specialist `index`, all `Manifest` sections (implicit from `specialties[]`), all `index.md` files in the bundle.

**Renamed:** none. v1 kept `worker_focus` / `verify` — v2 inherits them.

## File structure

```
plugins/dev-team/
  schemas/
    agenticteam.schema.json              # BUMP to v2
  scripts/
    tree_to_agenticteam.py               # emit v2 shape
    agenticteam_to_tree.py               # read v2 shape
  services/conductor/
    team_loader.py                       # read v2 fields (backward-compat fallback for v1 if cheap)
testing/unit/tests/agenticteam/
  test_schema_validation.py              # assert schema_version==2
  test_tree_to_bundle.py                 # assert new fields populated
  test_round_trip.py                     # v2 round-trip idempotent
  test_rollcall_parity.py                # still passes against regenerated bundles
teams/
  devteam.agenticteam/                   # regenerated
  puppynamingteam.agenticteam/           # regenerated
```

---

## Tasks

### Task 1 — Schema v2

- [ ] Rewrite `plugins/dev-team/schemas/agenticteam.schema.json`:
  - `schema_version` const `2`
  - top-level required: `kind`, `schema_version`, `name`, `specialists`
  - team-lead required: `name`, `role`
  - specialist required: `name`, `role`, `specialties`
  - specialty required: `name`, `worker_focus`
- [ ] Run `python3 -m json.tool plugins/dev-team/schemas/agenticteam.schema.json` — validates as JSON.
- [ ] Commit: `feat(agenticteam): schema v2 — structured section fields`.

### Task 2 — Converter

- [ ] Update `tree_to_agenticteam.py`:
  - `parse_markdown` returns frontmatter + `{ heading: text }` dict for H2 sections and sub-sections.
  - `_team_identity(team_root)` — read `team.md`, extract `## Role` → `role`.
  - `_team_lead(md)` — extract `## Role`, `## Persona` (+ `### Archetype` / `### Voice` / `### Priorities`), `## Phases` (list), `## Interaction Style` (list).
  - `_specialist(sp_dir)` — extract `## Role`, `## Persona`, `## Cookbook Sources` OR `## Sources` (list), `## Exploratory Prompts` (list).
  - `_specialty(md)` — extract `## Worker Focus`, `## Verify`. Stop emitting `body`.
  - Emit `schema_version: 2`. Drop all `index` fields and `Manifest` extraction.
  - Bundle output: stop copying `index.md` files; only copy resolved artifact files.
- [ ] Write `testing/unit/tests/agenticteam/test_section_extraction.py`: unit tests for `_team_lead`, `_specialist`, `_specialty` against synthetic markdown.
- [ ] Run: `pytest testing/unit/tests/agenticteam/test_section_extraction.py -v` → all pass.
- [ ] Commit: `feat(agenticteam): extract structured sections in tree_to_agenticteam`.

### Task 3 — Inverse converter

- [ ] Update `agenticteam_to_tree.py`:
  - For each team-lead → write `## Role`, `## Persona` (with sub-sections), `## Phases` (bulleted list), `## Interaction Style` (bulleted list).
  - For each specialist → write `## Role`, `## Persona`, `## Sources`, `## Exploratory Prompts`.
  - For each specialty → write `## Worker Focus`, `## Verify`.
  - For `team.md` → write `## Role`.
  - No `index.md` files written.
- [ ] Round-trip test in `test_round_trip.py`: tree → bundle (v2) → tree → bundle (v2), confirm second bundle equals first.
- [ ] Run: `pytest testing/unit/tests/agenticteam/test_round_trip.py -v` → pass.
- [ ] Commit: `feat(agenticteam): inverse converter reads v2`.

### Task 4 — Loader

- [ ] Update `services/conductor/team_loader.py::_load_from_agenticteam`:
  - Pull `worker_focus` and `verify` from v2 specialty fields as today.
  - No changes to `TeamManifest` / `SpecialtyDef` / `SpecialistDef` — loader just reads fewer legacy fields.
  - Reject bundles with `schema_version != 2` (keep the check strict; no silent v1 fallback).
- [ ] Run: `pytest testing/unit/tests/agenticteam/ testing/unit/tests/conductor/` → all pass.
- [ ] Commit: `feat(team-loader): read .agenticteam schema v2`.

### Task 5 — Regenerate live bundles

- [ ] Delete `teams/devteam.agenticteam/` and `teams/puppynamingteam.agenticteam/`.
- [ ] Regenerate:
  ```bash
  python3 plugins/dev-team/scripts/tree_to_agenticteam.py \
    teams/devteam teams/devteam.agenticteam \
    ~/projects/active/agenticcookbook/{guidelines,compliance,principles}

  python3 plugins/dev-team/scripts/tree_to_agenticteam.py \
    teams/puppynamingteam teams/puppynamingteam.agenticteam \
    ~/projects/active/agenticcookbook/{guidelines,compliance,principles}
  ```
- [ ] Spot-check: one devteam team-lead, one specialist, one specialty all have structured fields; no `body`; no `index.md`.
- [ ] Run: `pytest testing/unit/tests/` (affected suites) → green.
- [ ] Commit: `feat(teams): regenerate devteam + puppynamingteam bundles as schema v2`.

### Task 6 — Docs

- [ ] Update `docs/agenticteam-format.md`:
  - Replace the `team.json` example with v2 shape.
  - Document dropped fields in a "v1 → v2" section.
  - Note the `schema_version: 2` requirement.
- [ ] Commit: `docs: update agenticteam format reference for schema v2`.

---

## Done when

- All agenticteam + conductor tests green.
- `teams/*.agenticteam/team.json` is v2 with no `body`, no `index`, no `Manifest` sections.
- No `index.md` files inside any `.agenticteam/` dir.
- `docs/agenticteam-format.md` shows v2 example.
