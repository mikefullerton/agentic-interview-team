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
