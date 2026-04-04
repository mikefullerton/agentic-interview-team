#!/usr/bin/env python3
"""Milestone CRUD for markdown project-storage."""
import sys
from _lib import (
    parse_flags, require_flag, require_project,
    next_id, slugify, today_iso, read_frontmatter, read_body,
    write_item, update_item, json_output, json_build,
)


def create(flags):
    project = require_flag(flags, "project")
    name = require_flag(flags, "name")
    description = require_flag(flags, "description")
    status = require_flag(flags, "status")

    d = require_project(project)
    milestone_dir = d / "schedule"
    milestone_dir.mkdir(parents=True, exist_ok=True)

    item_id = next_id("milestone", milestone_dir)
    slug = slugify(name)
    file = milestone_dir / f"{item_id}-{slug}.md"

    target_date = flags.get("target_date") or None
    dependencies = flags.get("dependencies") or None

    metadata = {
        "id": item_id,
        "name": name,
        "status": status,
        "target_date": target_date,
        "dependencies": dependencies,
        "created": today_iso(),
        "modified": today_iso(),
    }

    write_item(file, description, metadata)
    json_build(id=item_id)


def get(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    milestone_dir = d / "schedule"

    matches = sorted(milestone_dir.glob(f"{item_id}-*.md")) if milestone_dir.is_dir() else []
    if not matches:
        print(f"Milestone not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    data = read_frontmatter(matches[0])
    body = read_body(matches[0])
    data["description"] = body
    json_output(data)


def list_all(flags):
    project = require_flag(flags, "project")

    d = require_project(project)
    milestone_dir = d / "schedule"
    milestone_dir.mkdir(parents=True, exist_ok=True)

    status_filter = flags.get("status", "")

    result = []
    for f in sorted(milestone_dir.glob("*.md")):
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
    milestone_dir = d / "schedule"

    matches = sorted(milestone_dir.glob(f"{item_id}-*.md")) if milestone_dir.is_dir() else []
    if not matches:
        print(f"Milestone not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    updates = {}
    if flags.get("name"):
        updates["name"] = flags["name"]
    if flags.get("status"):
        updates["status"] = flags["status"]
    if flags.get("target_date"):
        updates["target_date"] = flags["target_date"]
    if flags.get("dependencies"):
        updates["dependencies"] = flags["dependencies"]

    update_item(matches[0], updates)
    json_build(id=item_id)


def delete(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    milestone_dir = d / "schedule"

    matches = sorted(milestone_dir.glob(f"{item_id}-*.md")) if milestone_dir.is_dir() else []
    if not matches:
        print(f"Milestone not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    matches[0].unlink()
    json_build(id=item_id, deleted="true")


def main():
    if len(sys.argv) < 2:
        print("Usage: milestone.py <create|get|list|update|delete> [flags]", file=sys.stderr)
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
        print("Usage: milestone.py <create|get|list|update|delete> [flags]", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
