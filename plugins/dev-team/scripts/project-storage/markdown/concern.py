#!/usr/bin/env python3
"""Concern CRUD for markdown project-storage."""
import sys
from project_store import (
    parse_flags, require_flag, require_project,
    next_id, slugify, today_iso, read_frontmatter, read_body,
    write_item, update_item, json_output, json_build,
)


def create(flags):
    project = require_flag(flags, "project")
    title = require_flag(flags, "title")
    description = require_flag(flags, "description")
    raised_by = require_flag(flags, "raised_by")
    status = require_flag(flags, "status")

    d = require_project(project)
    concern_dir = d / "concerns"
    concern_dir.mkdir(parents=True, exist_ok=True)

    item_id = next_id("concern", concern_dir)
    slug = slugify(title)
    file = concern_dir / f"{item_id}-{slug}.md"

    related_to = flags.get("related_to") or None

    metadata = {
        "id": item_id,
        "title": title,
        "status": status,
        "raised_by": raised_by,
        "related_to": related_to,
        "created": today_iso(),
        "modified": today_iso(),
    }

    write_item(file, description, metadata)
    json_build(id=item_id)


def get(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    concern_dir = d / "concerns"

    matches = sorted(concern_dir.glob(f"{item_id}-*.md")) if concern_dir.is_dir() else []
    if not matches:
        print(f"Concern not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    data = read_frontmatter(matches[0])
    body = read_body(matches[0])
    data["description"] = body
    json_output(data)


def list_all(flags):
    project = require_flag(flags, "project")

    d = require_project(project)
    concern_dir = d / "concerns"
    concern_dir.mkdir(parents=True, exist_ok=True)

    status_filter = flags.get("status", "")

    result = []
    for f in sorted(concern_dir.glob("*.md")):
        if not f.is_file():
            continue
        data = read_frontmatter(f)
        if status_filter and data.get("status") != status_filter:
            continue
        result.append(data)

    json_output(result)


def update(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    concern_dir = d / "concerns"

    matches = sorted(concern_dir.glob(f"{item_id}-*.md")) if concern_dir.is_dir() else []
    if not matches:
        print(f"Concern not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    updates = {}
    if flags.get("title"):
        updates["title"] = flags["title"]
    if flags.get("status"):
        updates["status"] = flags["status"]
    if flags.get("raised_by"):
        updates["raised_by"] = flags["raised_by"]
    if flags.get("related_to"):
        updates["related_to"] = flags["related_to"]

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
    concern_dir = d / "concerns"

    matches = sorted(concern_dir.glob(f"{item_id}-*.md")) if concern_dir.is_dir() else []
    if not matches:
        print(f"Concern not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    matches[0].unlink()
    json_build(id=item_id, deleted="true")


def main():
    if len(sys.argv) < 2:
        print("Usage: concern.py <create|get|list|update|delete> [flags]", file=sys.stderr)
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
        print("Usage: concern.py <create|get|list|update|delete> [flags]", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
