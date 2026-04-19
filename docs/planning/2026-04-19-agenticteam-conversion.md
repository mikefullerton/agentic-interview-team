# `.agenticteam` Bundle Format — Conversion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a self-enclosed team-bundle format (`<team>.agenticteam/` directory containing `team.json` + real reference files) as a second accepted on-disk shape for teams, convert both live teams (`devteam`, `puppynamingteam`), and keep the existing markdown-tree shape working unchanged.

**Architecture:** The bundle is a directory: `team.json` + subtrees (`guidelines/`, `compliance/`, `principles/`) of real markdown files at their declared `artifact:` paths. No inline blobs. A loader sniffer picks bundle-vs-tree at `load_team` time. Runtime model (`TeamManifest`) stays the same — bundle is an alternate disk form, not a new runtime type.

**Tech Stack:** Python 3.10+, stdlib `json` + `pathlib` + `shutil`, pytest.

**Out of scope (deferred):**
- Zipping `.agenticteam` into a single distributable file.
- macOS UTI / extension registration.
- Removing the markdown-tree path (Phase 5 cutover, tracked separately).

---

## File Structure

```
plugins/dev-team/
  schemas/
    agenticteam.schema.json        # JSON-schema for team.json
  scripts/
    tree_to_agenticteam.py         # markdown tree  →  .agenticteam bundle
    agenticteam_to_tree.py         # .agenticteam   →  markdown tree (round-trip)
  services/conductor/
    team_loader.py                 # +sniff: `.agenticteam` / `team.json` root
  services/rollcall/
    discovery.py                   # RoleRef.path → RoleRef.definition_text
teams/
  devteam.agenticteam/             # generated bundle (committed)
  puppynamingteam.agenticteam/     # generated bundle (committed)
testing/unit/tests/agenticteam/
  __init__.py
  conftest.py                      # fixture: reference roots + tmp bundle dir
  test_tree_to_bundle.py           # parse + seal + files on disk
  test_bundle_to_tree.py           # inverse
  test_round_trip.py               # tree → bundle → tree (idempotent)
  test_schema_validation.py        # generated team.json conforms to schema
  test_loader_sniffer.py           # load_team picks bundle/tree correctly
  test_rollcall_parity.py          # rollcall yields identical roles
```

---

## Task 1: Schema + scripts directory scaffolding

**Files:**
- Create: `plugins/dev-team/schemas/agenticteam.schema.json`

- [ ] **Step 1: Write the schema**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://agenticdevteam/schemas/agenticteam.json",
  "title": "AgenticTeam",
  "type": "object",
  "required": ["kind", "schema_version", "name", "specialists"],
  "properties": {
    "kind": { "const": "agenticteam" },
    "schema_version": { "const": 1 },
    "name": { "type": "string", "minLength": 1 },
    "identity": { "type": "string" },
    "index": { "type": "string" },
    "team_leads": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name"],
        "properties": {
          "name": { "type": "string" },
          "frontmatter": { "type": "object" },
          "body": { "type": "string" }
        }
      }
    },
    "specialists": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "specialties"],
        "properties": {
          "name": { "type": "string" },
          "description": { "type": "string" },
          "frontmatter": { "type": "object" },
          "index": { "type": "string" },
          "specialties": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["name"],
              "properties": {
                "name": { "type": "string" },
                "frontmatter": { "type": "object" },
                "worker_focus": { "type": "string" },
                "verify": { "type": "string" },
                "body": { "type": "string" },
                "artifact_kind": {
                  "enum": ["reference", "reference_unresolved", "output_location"]
                }
              }
            }
          }
        }
      }
    },
    "consulting": { "type": "array" }
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add plugins/dev-team/schemas/agenticteam.schema.json
git commit -m "feat(agenticteam): add JSON schema for team.json bundles"
```

---

## Task 2: `tree_to_agenticteam.py` — converter script

**Files:**
- Create: `plugins/dev-team/scripts/tree_to_agenticteam.py`

- [ ] **Step 1: Write the script**

Port `/tmp/team_to_json.py` + `/tmp/bundle_team.py` into a single script. The full source:

```python
"""Convert a teams/<name>/ markdown tree into a <name>.agenticteam/ bundle.

Bundle layout:
    <team>.agenticteam/
        team.json
        guidelines/...          (real markdown files at declared paths)
        compliance/...
        principles/...

Run:
    tree_to_agenticteam.py <team_root> <bundle_dir> <ref-root>...
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def parse_markdown(path: Path) -> tuple[dict, str]:
    if not path.is_file():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text.strip()
    fm_raw, body = m.group(1), m.group(2)
    fm: dict = {}
    for line in fm_raw.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        fm[k.strip()] = v.strip()
    return fm, body.strip()


def split_sections(body: str) -> dict[str, str]:
    out: dict[str, str] = {}
    matches = list(SECTION_RE.finditer(body))
    if not matches:
        if body.strip():
            out["_body"] = body.strip()
        return out
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        out[m.group(1).strip()] = body[start:end].strip()
    pre = body[: matches[0].start()].strip()
    if pre:
        out["_preamble"] = pre
    return out


def _specialty(path: Path) -> dict:
    fm, body = parse_markdown(path)
    sections = split_sections(body)
    return {
        "name": path.stem,
        "frontmatter": fm,
        "worker_focus": sections.get("Worker Focus", ""),
        "verify": sections.get("Verify", ""),
        "body": body,
    }


def _specialist(sp_dir: Path) -> dict:
    fm, body = parse_markdown(sp_dir / "specialist.md")
    _, idx = parse_markdown(sp_dir / "index.md")
    specialties: list[dict] = []
    for cand in ("specialities", "specialties"):
        d = sp_dir / cand
        if not d.is_dir():
            continue
        for md in sorted(d.iterdir()):
            if md.suffix != ".md" or md.name == "index.md":
                continue
            specialties.append(_specialty(md))
        break
    return {
        "name": sp_dir.name,
        "frontmatter": fm,
        "description": body,
        "index": idx,
        "specialties": specialties,
    }


def _team_lead(path: Path) -> dict:
    fm, body = parse_markdown(path)
    return {"name": path.stem, "frontmatter": fm, "body": body}


def _consulting(node: Path) -> list[dict]:
    out: list[dict] = []
    for entry in sorted(node.iterdir()):
        if entry.is_file() and entry.suffix == ".md":
            if entry.name == "index.md":
                continue
            _, body = parse_markdown(entry)
            out.append({"name": entry.stem, "body": body})
        elif entry.is_dir():
            _, idx = parse_markdown(entry / "index.md")
            out.append({
                "name": entry.name,
                "index": idx,
                "children": _consulting(entry),
            })
    return out


def convert_team(team_root: Path) -> dict:
    _, identity = parse_markdown(team_root / "team.md")
    _, index = parse_markdown(team_root / "index.md")
    leads: list[dict] = []
    lead_dir = team_root / "team-leads"
    if lead_dir.is_dir():
        for md in sorted(lead_dir.iterdir()):
            if md.suffix != ".md" or md.name == "index.md":
                continue
            leads.append(_team_lead(md))
    specialists: list[dict] = []
    sp_root = team_root / "specialists"
    if sp_root.is_dir():
        for sp_dir in sorted(sp_root.iterdir()):
            if not sp_dir.is_dir():
                continue
            specialists.append(_specialist(sp_dir))
    consulting_root = team_root / "consulting"
    consulting = _consulting(consulting_root) if consulting_root.is_dir() else []
    return {
        "kind": "agenticteam",
        "schema_version": 1,
        "name": team_root.name,
        "identity": identity,
        "index": index,
        "team_leads": leads,
        "specialists": specialists,
        "consulting": consulting,
    }


def index_reference_roots(roots: list[Path]) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = defaultdict(list)
    for root in roots:
        if not root.is_dir():
            continue
        for f in root.rglob("*.md"):
            rel = f.relative_to(root.parent)
            parts = rel.parts
            for i in range(len(parts)):
                index["/".join(parts[i:])].append(f)
    return index


def resolve_artifact(path: str, index: dict[str, list[Path]]) -> Path | None:
    if path.endswith("/"):
        return None
    hits = index.get(path)
    if hits:
        return hits[0]
    parts = path.split("/")
    for i in range(1, len(parts)):
        hits = index.get("/".join(parts[i:]))
        if hits:
            return hits[0]
    return None


def seal_bundle(
    team_doc: dict,
    reference_roots: list[Path],
    bundle_dir: Path,
) -> dict[str, int]:
    stats = {k: 0 for k in (
        "specialties_total", "with_artifact", "output_locations",
        "resolved", "unresolved", "files_copied",
    )}
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True)
    index = index_reference_roots(reference_roots)
    copied: set[str] = set()
    for specialist in team_doc.get("specialists", []):
        for specialty in specialist.get("specialties", []):
            stats["specialties_total"] += 1
            artifact = (specialty.get("frontmatter") or {}).get("artifact")
            if not artifact:
                continue
            stats["with_artifact"] += 1
            if artifact.endswith("/"):
                stats["output_locations"] += 1
                specialty["artifact_kind"] = "output_location"
                continue
            resolved = resolve_artifact(artifact, index)
            if resolved is None:
                stats["unresolved"] += 1
                specialty["artifact_kind"] = "reference_unresolved"
                continue
            stats["resolved"] += 1
            specialty["artifact_kind"] = "reference"
            if artifact in copied:
                continue
            dest = bundle_dir / artifact
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(resolved, dest)
            copied.add(artifact)
            stats["files_copied"] += 1
    (bundle_dir / "team.json").write_text(
        json.dumps(team_doc, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return stats


def main() -> int:
    if len(sys.argv) < 4:
        print(
            "usage: tree_to_agenticteam.py <team_root> <bundle_dir> <ref-root>...",
            file=sys.stderr,
        )
        return 2
    team_root = Path(sys.argv[1]).resolve()
    bundle_dir = Path(sys.argv[2])
    roots = [Path(p).resolve() for p in sys.argv[3:]]
    team_doc = convert_team(team_root)
    stats = seal_bundle(team_doc, roots, bundle_dir)
    print(f"  bundle: {bundle_dir}")
    for k, v in stats.items():
        print(f"    {k:22s} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Smoke-test against puppynamingteam**

```bash
python3 plugins/dev-team/scripts/tree_to_agenticteam.py \
  teams/puppynamingteam \
  /tmp/puppy.agenticteam \
  ~/projects/active/agenticcookbook/guidelines \
  ~/projects/active/agenticcookbook/compliance \
  ~/projects/active/agenticcookbook/principles
ls /tmp/puppy.agenticteam/team.json && rm -rf /tmp/puppy.agenticteam
```

Expected: `team.json` exists, stats print with non-zero `specialties_total`.

- [ ] **Step 3: Commit**

```bash
git add plugins/dev-team/scripts/tree_to_agenticteam.py
git commit -m "feat(agenticteam): tree_to_agenticteam converter + bundle sealer"
```

---

## Task 3: `agenticteam_to_tree.py` — inverse converter

**Files:**
- Create: `plugins/dev-team/scripts/agenticteam_to_tree.py`

- [ ] **Step 1: Write the inverse**

```python
"""Inverse of tree_to_agenticteam: write a .agenticteam bundle back as a
teams/<name>/ markdown tree. Used by round-trip tests; not part of the
loader path.

Run:
    agenticteam_to_tree.py <bundle_dir> <team_root>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _fmt_frontmatter(fm: dict) -> str:
    if not fm:
        return ""
    lines = [f"{k}: {v}" for k, v in fm.items()]
    return "---\n" + "\n".join(lines) + "\n---\n"


def _write_md(path: Path, frontmatter: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = _fmt_frontmatter(frontmatter or {})
    payload = fm + (body or "")
    path.write_text(payload, encoding="utf-8")


def write_tree(team_doc: dict, team_root: Path) -> None:
    team_root.mkdir(parents=True, exist_ok=True)
    if team_doc.get("identity"):
        _write_md(team_root / "team.md", {}, team_doc["identity"])
    if team_doc.get("index"):
        _write_md(team_root / "index.md", {}, team_doc["index"])
    for lead in team_doc.get("team_leads", []):
        _write_md(
            team_root / "team-leads" / f"{lead['name']}.md",
            lead.get("frontmatter") or {},
            lead.get("body") or "",
        )
    for sp in team_doc.get("specialists", []):
        sp_dir = team_root / "specialists" / sp["name"]
        if sp.get("description"):
            _write_md(
                sp_dir / "specialist.md",
                sp.get("frontmatter") or {},
                sp["description"],
            )
        if sp.get("index"):
            _write_md(sp_dir / "index.md", {}, sp["index"])
        for st in sp.get("specialties", []):
            _write_md(
                sp_dir / "specialities" / f"{st['name']}.md",
                st.get("frontmatter") or {},
                st.get("body") or "",
            )


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: agenticteam_to_tree.py <bundle_dir> <team_root>",
            file=sys.stderr,
        )
        return 2
    bundle_dir = Path(sys.argv[1]).resolve()
    team_root = Path(sys.argv[2])
    team_doc = json.loads(
        (bundle_dir / "team.json").read_text(encoding="utf-8")
    )
    write_tree(team_doc, team_root)
    print(f"  wrote tree: {team_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Commit**

```bash
git add plugins/dev-team/scripts/agenticteam_to_tree.py
git commit -m "feat(agenticteam): inverse agenticteam_to_tree converter"
```

---

## Task 4: Conversion contract tests

**Files:**
- Create: `testing/unit/tests/agenticteam/__init__.py`
- Create: `testing/unit/tests/agenticteam/conftest.py`
- Create: `testing/unit/tests/agenticteam/test_tree_to_bundle.py`
- Create: `testing/unit/tests/agenticteam/test_round_trip.py`
- Create: `testing/unit/tests/agenticteam/test_schema_validation.py`

- [ ] **Step 1: Package marker**

`testing/unit/tests/agenticteam/__init__.py` — empty.

- [ ] **Step 2: conftest**

```python
"""Fixtures for agenticteam conversion tests."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = REPO_ROOT / "plugins" / "dev-team" / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, SCRIPTS / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def tree_to_agenticteam():
    return _load("tree_to_agenticteam")


@pytest.fixture
def agenticteam_to_tree():
    return _load("agenticteam_to_tree")


@pytest.fixture
def mini_team(tmp_path: Path) -> Path:
    """Build a minimal valid teams/<name>/ tree on disk."""
    root = tmp_path / "toyteam"
    (root / "team-leads").mkdir(parents=True)
    (root / "specialists" / "alpha" / "specialities").mkdir(parents=True)
    (root / "team.md").write_text("# Toy Team\nWe do toys.", encoding="utf-8")
    (root / "team-leads" / "lead.md").write_text(
        "---\nrole: lead\n---\n# Lead\nLeads.", encoding="utf-8",
    )
    (root / "specialists" / "alpha" / "specialist.md").write_text(
        "---\nname: alpha\n---\nAlpha specialist.", encoding="utf-8",
    )
    (root / "specialists" / "alpha" / "specialities" / "one.md").write_text(
        "---\nname: one\nartifact: guidelines/toys.md\n---\n"
        "## Worker Focus\nBuild toys.\n\n## Verify\nToys pass.",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def mini_refs(tmp_path: Path) -> list[Path]:
    """Reference pool containing one guideline file."""
    g = tmp_path / "refs" / "guidelines"
    g.mkdir(parents=True)
    (g / "toys.md").write_text("# Toys\nAll about toys.", encoding="utf-8")
    return [tmp_path / "refs"]
```

- [ ] **Step 3: `test_tree_to_bundle.py`**

```python
"""tree_to_agenticteam produces a bundle dir with team.json + sealed refs."""
from __future__ import annotations

import json
from pathlib import Path


def test_bundle_has_team_json_and_required_fields(
    tree_to_agenticteam, mini_team, mini_refs, tmp_path
):
    bundle = tmp_path / "toy.agenticteam"
    doc = tree_to_agenticteam.convert_team(mini_team)
    tree_to_agenticteam.seal_bundle(doc, mini_refs, bundle)

    data = json.loads((bundle / "team.json").read_text())
    assert data["kind"] == "agenticteam"
    assert data["schema_version"] == 1
    assert data["name"] == "toyteam"
    assert len(data["specialists"]) == 1
    assert data["specialists"][0]["specialties"][0]["artifact_kind"] == "reference"


def test_bundle_copies_referenced_files_at_declared_paths(
    tree_to_agenticteam, mini_team, mini_refs, tmp_path
):
    bundle = tmp_path / "toy.agenticteam"
    doc = tree_to_agenticteam.convert_team(mini_team)
    stats = tree_to_agenticteam.seal_bundle(doc, mini_refs, bundle)

    assert stats["resolved"] == 1
    assert stats["unresolved"] == 0
    assert stats["files_copied"] == 1
    assert (bundle / "guidelines" / "toys.md").is_file()


def test_unresolved_artifact_marked_and_no_file_copied(
    tree_to_agenticteam, mini_team, tmp_path
):
    """Empty ref pool → artifact unresolvable → marked, no file copy."""
    bundle = tmp_path / "toy.agenticteam"
    doc = tree_to_agenticteam.convert_team(mini_team)
    stats = tree_to_agenticteam.seal_bundle(doc, [], bundle)
    assert stats["unresolved"] == 1
    assert stats["files_copied"] == 0
    assert not (bundle / "guidelines").exists()
    kinds = [
        s["artifact_kind"]
        for sp in doc["specialists"] for s in sp["specialties"]
    ]
    assert kinds == ["reference_unresolved"]
```

- [ ] **Step 4: `test_round_trip.py`**

```python
"""tree → bundle → tree preserves the team's structural content."""
from __future__ import annotations

from pathlib import Path


def _relpaths(root: Path) -> set[str]:
    return {
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file() and not p.name.startswith(".")
    }


def test_round_trip_preserves_markdown_layout(
    tree_to_agenticteam, agenticteam_to_tree, mini_team, mini_refs, tmp_path
):
    bundle = tmp_path / "toy.agenticteam"
    doc = tree_to_agenticteam.convert_team(mini_team)
    tree_to_agenticteam.seal_bundle(doc, mini_refs, bundle)

    restored = tmp_path / "restored"
    import json
    team_doc = json.loads((bundle / "team.json").read_text())
    agenticteam_to_tree.write_tree(team_doc, restored)

    tracked_src = {
        p for p in _relpaths(mini_team)
        if not p.startswith("index.md") and "team-leads/index.md" not in p
    }
    tracked_dst = _relpaths(restored)
    # Every specialty / specialist / team file round-trips.
    for path in tracked_src:
        assert path in tracked_dst, f"missing after round-trip: {path}"


def test_round_trip_preserves_specialty_frontmatter_and_sections(
    tree_to_agenticteam, agenticteam_to_tree, mini_team, mini_refs, tmp_path
):
    bundle = tmp_path / "toy.agenticteam"
    doc = tree_to_agenticteam.convert_team(mini_team)
    tree_to_agenticteam.seal_bundle(doc, mini_refs, bundle)

    restored = tmp_path / "restored"
    import json
    team_doc = json.loads((bundle / "team.json").read_text())
    agenticteam_to_tree.write_tree(team_doc, restored)

    specialty = (
        restored / "specialists" / "alpha" / "specialities" / "one.md"
    ).read_text(encoding="utf-8")
    assert "artifact: guidelines/toys.md" in specialty
    assert "## Worker Focus" in specialty
    assert "## Verify" in specialty
```

- [ ] **Step 5: `test_schema_validation.py`**

```python
"""team.json conforms to agenticteam.schema.json. Uses stdlib-only structural checks
to avoid pulling in jsonschema as a dependency."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA = json.loads(
    (REPO_ROOT / "plugins" / "dev-team" / "schemas" / "agenticteam.schema.json")
    .read_text(encoding="utf-8")
)


def _required(obj, keys, label):
    missing = [k for k in keys if k not in obj]
    assert not missing, f"{label} missing {missing}"


def test_generated_team_json_has_required_top_level_fields(
    tree_to_agenticteam, mini_team, mini_refs, tmp_path
):
    bundle = tmp_path / "toy.agenticteam"
    doc = tree_to_agenticteam.convert_team(mini_team)
    tree_to_agenticteam.seal_bundle(doc, mini_refs, bundle)

    data = json.loads((bundle / "team.json").read_text())
    _required(data, SCHEMA["required"], "team.json")
    assert data["kind"] == SCHEMA["properties"]["kind"]["const"]
    assert data["schema_version"] == SCHEMA["properties"]["schema_version"]["const"]


def test_every_specialty_has_name(tree_to_agenticteam, mini_team, mini_refs, tmp_path):
    bundle = tmp_path / "toy.agenticteam"
    doc = tree_to_agenticteam.convert_team(mini_team)
    tree_to_agenticteam.seal_bundle(doc, mini_refs, bundle)
    data = json.loads((bundle / "team.json").read_text())
    for sp in data["specialists"]:
        _required(sp, ["name", "specialties"], f"specialist {sp.get('name')}")
        for st in sp["specialties"]:
            _required(st, ["name"], f"specialty in {sp['name']}")
```

- [ ] **Step 6: Run all conversion tests**

```bash
cd /Users/mfullerton/projects/active/agenticdevteam/.claude/worktrees/agenticteam-format
python3 -m pytest testing/unit/tests/agenticteam/ -v
```

Expected: 7 passed (3 + 2 + 2).

- [ ] **Step 7: Commit**

```bash
git add testing/unit/tests/agenticteam/
git commit -m "test(agenticteam): round-trip + schema + bundle-seal contract tests"
```

---

## Task 5: `team_loader` sniffer — accept `.agenticteam` bundles

**Files:**
- Modify: `plugins/dev-team/services/conductor/team_loader.py`
- Create: `testing/unit/tests/agenticteam/test_loader_sniffer.py`

Read the full file first so the edit targets the actual `load_team` signature.

- [ ] **Step 1: Read current loader**

```bash
cat plugins/dev-team/services/conductor/team_loader.py | head -200
```

Note the exact function names and where `load_team` / the dispatcher lives. If the loader is `load_team(team_root: Path) -> TeamManifest`, the sniffer goes at the top of that function. If it's named differently, keep the existing name and only add the branch.

- [ ] **Step 2: Add `_load_from_agenticteam`**

At the end of `team_loader.py`, append:

```python
import json as _json


def _load_from_agenticteam(bundle_root: Path) -> "TeamManifest":
    """Build a TeamManifest from a <name>.agenticteam/ bundle (team.json)."""
    team_json = bundle_root / "team.json"
    doc = _json.loads(team_json.read_text(encoding="utf-8"))
    if doc.get("kind") != "agenticteam":
        raise ValueError(
            f"{team_json}: expected kind=agenticteam, got {doc.get('kind')!r}"
        )
    manifest = TeamManifest(name=doc["name"], team_root=bundle_root)
    for sp in doc.get("specialists", []):
        sd = SpecialistDef(name=sp["name"])
        for st in sp.get("specialties", []):
            fm = st.get("frontmatter") or {}
            sd.specialties[st["name"]] = SpecialtyDef(
                name=st["name"],
                description=(fm.get("description") or ""),
                worker_focus=st.get("worker_focus", ""),
                verify=st.get("verify", ""),
                logical_model=fm.get("logical_model", "balanced"),
            )
        manifest.specialists[sp["name"]] = sd
    return manifest
```

- [ ] **Step 3: Route `load_team` through the sniffer**

Find the existing `load_team` definition and replace its first line with a sniff. Example patch (adjust to the real signature):

```python
def load_team(team_root: Path) -> TeamManifest:
    team_root = team_root.resolve()
    if team_root.suffix == ".agenticteam" or (team_root / "team.json").is_file():
        return _load_from_agenticteam(team_root)
    # ... existing markdown-tree path continues unchanged ...
```

- [ ] **Step 4: Write the sniffer test**

`testing/unit/tests/agenticteam/test_loader_sniffer.py`:

```python
"""`load_team` picks the agenticteam loader when the root is a bundle."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))

from services.conductor.team_loader import load_team  # noqa: E402


def test_load_team_reads_bundle(
    tree_to_agenticteam, mini_team, mini_refs, tmp_path
):
    bundle = tmp_path / "toy.agenticteam"
    doc = tree_to_agenticteam.convert_team(mini_team)
    tree_to_agenticteam.seal_bundle(doc, mini_refs, bundle)

    manifest = load_team(bundle)
    assert manifest.name == "toyteam"
    assert "alpha" in manifest.specialists
    assert "one" in manifest.specialists["alpha"].specialties
    assert manifest.specialists["alpha"].specialties["one"].worker_focus \
        == "Build toys."


def test_load_team_still_reads_markdown_tree(mini_team):
    manifest = load_team(mini_team)
    assert manifest.name == "toyteam"
    assert "alpha" in manifest.specialists
```

- [ ] **Step 5: Run the sniffer test**

```bash
python3 -m pytest testing/unit/tests/agenticteam/test_loader_sniffer.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add plugins/dev-team/services/conductor/team_loader.py \
        testing/unit/tests/agenticteam/test_loader_sniffer.py
git commit -m "feat(team-loader): load from .agenticteam bundles via team.json sniff"
```

---

## Task 6: RoleRef — replace `path: Path` with `definition_text: str`

**Files:**
- Modify: `plugins/dev-team/services/rollcall/discovery.py`

**Why now:** `role.path` is currently declared and set but not read. Replacing it with pre-loaded text removes the on-disk-format leak from runtime so a future bundle-based discovery can construct `RoleRef`s without handing out paths that only make sense for markdown trees.

- [ ] **Step 1: Edit `discovery.py`**

Replace the `RoleRef` definition and the two call sites that set `path=md`:

```python
@dataclass(frozen=True)
class RoleRef:
    team: str
    kind: RoleKind
    name: str
    definition_text: str
```

At each `path=md` construction, change to `definition_text=md.read_text(encoding="utf-8")`. Both `_discover_team_leads` and `_discover_specialty_roles` need this update.

- [ ] **Step 2: Run existing rollcall tests**

```bash
python3 -m pytest testing/unit/tests/conductor/rollcall/ -v
```

Expected: existing tests still pass (no caller reads `.path`).

- [ ] **Step 3: Commit**

```bash
git add plugins/dev-team/services/rollcall/discovery.py
git commit -m "refactor(rollcall): RoleRef.path → RoleRef.definition_text"
```

---

## Task 7: Generate `.agenticteam` bundles for live teams

**Files:**
- Create: `teams/puppynamingteam.agenticteam/` (bundle)
- Create: `teams/devteam.agenticteam/` (bundle)

- [ ] **Step 1: Generate puppynamingteam bundle**

```bash
python3 plugins/dev-team/scripts/tree_to_agenticteam.py \
  teams/puppynamingteam \
  teams/puppynamingteam.agenticteam \
  ~/projects/active/agenticcookbook/guidelines \
  ~/projects/active/agenticcookbook/compliance \
  ~/projects/active/agenticcookbook/principles
```

Expected: `teams/puppynamingteam.agenticteam/team.json` exists; `unresolved` is 0 (or report to user if >0).

- [ ] **Step 2: Generate devteam bundle**

```bash
python3 plugins/dev-team/scripts/tree_to_agenticteam.py \
  teams/devteam \
  teams/devteam.agenticteam \
  ~/projects/active/agenticcookbook/guidelines \
  ~/projects/active/agenticcookbook/compliance \
  ~/projects/active/agenticcookbook/principles
```

Expected: `teams/devteam.agenticteam/team.json` exists. Prior prototype reported 243 specialties / 169 unique refs / 0 unresolved — confirm parity.

- [ ] **Step 3: Confirm size + structure**

```bash
du -sh teams/devteam.agenticteam teams/puppynamingteam.agenticteam
find teams/devteam.agenticteam -maxdepth 1 -type d
```

- [ ] **Step 4: Commit the bundles**

```bash
git add teams/puppynamingteam.agenticteam teams/devteam.agenticteam
git commit -m "feat(teams): add .agenticteam bundles for devteam + puppynamingteam"
```

---

## Task 8: Rollcall parity test — bundle discovery matches tree discovery

**Files:**
- Create: `testing/unit/tests/agenticteam/test_rollcall_parity.py`

**Goal:** once a `discover_team` equivalent exists for bundles (or tree-discovery is adapted to accept a bundle root), both should yield the same role set. Until bundle discovery lands, this test asserts the intermediate property that `load_team` over the bundle produces the same `TeamManifest.specialists` keys as `load_team` over the tree.

- [ ] **Step 1: Write the parity test**

```python
"""A team's .agenticteam bundle and its source markdown tree load into
equivalent TeamManifests."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "dev-team"))

from services.conductor.team_loader import load_team  # noqa: E402


def _manifest_shape(manifest):
    return {
        sp: sorted(sd.specialties.keys())
        for sp, sd in manifest.specialists.items()
    }


def test_puppynamingteam_bundle_matches_tree():
    tree = REPO_ROOT / "teams" / "puppynamingteam"
    bundle = REPO_ROOT / "teams" / "puppynamingteam.agenticteam"
    if not bundle.exists():
        import pytest
        pytest.skip("bundle not generated yet")
    assert _manifest_shape(load_team(tree)) == _manifest_shape(load_team(bundle))


def test_devteam_bundle_matches_tree():
    tree = REPO_ROOT / "teams" / "devteam"
    bundle = REPO_ROOT / "teams" / "devteam.agenticteam"
    if not bundle.exists():
        import pytest
        pytest.skip("bundle not generated yet")
    assert _manifest_shape(load_team(tree)) == _manifest_shape(load_team(bundle))
```

- [ ] **Step 2: Run parity test**

```bash
python3 -m pytest testing/unit/tests/agenticteam/test_rollcall_parity.py -v
```

Expected: 2 passed.

- [ ] **Step 3: Commit**

```bash
git add testing/unit/tests/agenticteam/test_rollcall_parity.py
git commit -m "test(agenticteam): parity between tree and bundle TeamManifest shape"
```

---

## Final Verification

- [ ] **Step 1: Run the full agenticteam suite**

```bash
python3 -m pytest testing/unit/tests/agenticteam/ -v
```

Expected: 11 passed (3 + 2 + 2 + 2 + 2).

- [ ] **Step 2: Spot-check that the existing test matrix still passes**

```bash
python3 -m pytest testing/unit/tests/conductor/ testing/unit/tests/atp/ -q
```

Expected: no new failures. Any pre-existing `asyncio.get_event_loop()` warnings on Python 3.9 are environment-related (plan requires 3.10+).

- [ ] **Step 3: Finish the branch**

Use the **superpowers:finishing-a-development-branch** skill: verify tests pass, then present merge/PR options.

---

## Deferred (Phase 5 — separate plan)

- Retire `teams/<name>/` markdown trees (make `.agenticteam` the only accepted form). Requires a migration pass for external authoring skills and a grace-period window where both load.
- Zip `.agenticteam` → single-file distribution.
- macOS UTI registration and `.agenticteam` Finder iconography.
