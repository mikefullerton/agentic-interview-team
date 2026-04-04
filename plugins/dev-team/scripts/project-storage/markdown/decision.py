#!/usr/bin/env python3
"""Decision CRUD for markdown project-storage."""
import sys
from _lib import (
    parse_flags, require_flag, require_project,
    next_id, slugify, today_iso, read_frontmatter, read_body,
    write_item, update_item, json_output, json_build,
)


def create(flags):
    project = require_flag(flags, "project")
    title = require_flag(flags, "title")
    description = require_flag(flags, "description")
    rationale = require_flag(flags, "rationale")
    made_by = require_flag(flags, "made_by")

    d = require_project(project)
    decision_dir = d / "decisions"
    decision_dir.mkdir(parents=True, exist_ok=True)

    item_id = next_id("decision", decision_dir)
    slug = slugify(title)
    file = decision_dir / f"{item_id}-{slug}.md"

    alternatives = flags.get("alternatives") or None
    decision_date = flags.get("date") or today_iso()

    metadata = {
        "id": item_id,
        "title": title,
        "rationale": rationale,
        "alternatives": alternatives,
        "made_by": made_by,
        "date": decision_date,
        "created": today_iso(),
        "modified": today_iso(),
    }

    write_item(file, description, metadata)
    json_build(id=item_id)


def get(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    decision_dir = d / "decisions"

    matches = sorted(decision_dir.glob(f"{item_id}-*.md")) if decision_dir.is_dir() else []
    if not matches:
        print(f"Decision not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    data = read_frontmatter(matches[0])
    body = read_body(matches[0])
    data["description"] = body
    json_output(data)


def list_all(flags):
    project = require_flag(flags, "project")

    d = require_project(project)
    decision_dir = d / "decisions"
    decision_dir.mkdir(parents=True, exist_ok=True)

    result = []
    for f in sorted(decision_dir.glob("*.md")):
        if not f.is_file():
            continue
        data = read_frontmatter(f)
        result.append(data)

    json_output(result)


def update(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    decision_dir = d / "decisions"

    matches = sorted(decision_dir.glob(f"{item_id}-*.md")) if decision_dir.is_dir() else []
    if not matches:
        print(f"Decision not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    updates = {}
    if flags.get("title"):
        updates["title"] = flags["title"]
    if flags.get("rationale"):
        updates["rationale"] = flags["rationale"]
    if flags.get("alternatives"):
        updates["alternatives"] = flags["alternatives"]
    if flags.get("made_by"):
        updates["made_by"] = flags["made_by"]
    if flags.get("date"):
        updates["date"] = flags["date"]

    description = flags.get("description", "")
    if description:
        current = read_frontmatter(matches[0])
        current.update(updates)
        current["modified"] = today_iso()
        write_item(matches[0], description, current)
    else:
        update_item(matches[0], updates)

    json_build(id=item_id)


def delete(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    decision_dir = d / "decisions"

    matches = sorted(decision_dir.glob(f"{item_id}-*.md")) if decision_dir.is_dir() else []
    if not matches:
        print(f"Decision not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    matches[0].unlink()
    json_build(id=item_id, deleted="true")


def main():
    if len(sys.argv) < 2:
        print("Usage: decision.py <create|get|list|update|delete> [flags]", file=sys.stderr)
        sys.exit(1)
    action = sys.argv[1]
    flags = parse_flags(sys.argv[2:])

    actions = {
        "create": create,
        "get": get,
        "list": list_all,
        "update": update,
        "delete": delete,
    }
    if action not in actions:
        print(f"Unknown action: {action}", file=sys.stderr)
        print("Usage: decision.py <create|get|list|update|delete> [flags]", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
