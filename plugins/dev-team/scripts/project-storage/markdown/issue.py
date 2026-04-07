#!/usr/bin/env python3
"""Issue CRUD for markdown project-storage."""
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
    severity = require_flag(flags, "severity")
    status = require_flag(flags, "status")

    d = require_project(project)
    issue_dir = d / "issues"
    issue_dir.mkdir(parents=True, exist_ok=True)

    item_id = next_id("issue", issue_dir)
    slug = slugify(title)
    file = issue_dir / f"{item_id}-{slug}.md"

    source = flags.get("source") or None
    related_findings = flags.get("related_findings") or None

    metadata = {
        "id": item_id,
        "title": title,
        "status": status,
        "severity": severity,
        "source": source,
        "related_findings": related_findings,
        "created": today_iso(),
        "modified": today_iso(),
    }

    write_item(file, description, metadata)
    json_build(id=item_id)


def get(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    issue_dir = d / "issues"

    matches = sorted(issue_dir.glob(f"{item_id}-*.md")) if issue_dir.is_dir() else []
    if not matches:
        print(f"Issue not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    data = read_frontmatter(matches[0])
    body = read_body(matches[0])
    data["description"] = body
    json_output(data)


def list_all(flags):
    project = require_flag(flags, "project")

    d = require_project(project)
    issue_dir = d / "issues"
    issue_dir.mkdir(parents=True, exist_ok=True)

    status_filter = flags.get("status", "")
    severity_filter = flags.get("severity", "")

    result = []
    for f in sorted(issue_dir.glob("*.md")):
        if not f.is_file():
            continue
        data = read_frontmatter(f)
        if status_filter and data.get("status") != status_filter:
            continue
        if severity_filter and data.get("severity") != severity_filter:
            continue
        result.append(data)

    json_output(result)


def update(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    issue_dir = d / "issues"

    matches = sorted(issue_dir.glob(f"{item_id}-*.md")) if issue_dir.is_dir() else []
    if not matches:
        print(f"Issue not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    updates = {}
    if flags.get("title"):
        updates["title"] = flags["title"]
    if flags.get("status"):
        updates["status"] = flags["status"]
    if flags.get("severity"):
        updates["severity"] = flags["severity"]
    if flags.get("source"):
        updates["source"] = flags["source"]
    if flags.get("related_findings"):
        updates["related_findings"] = flags["related_findings"]

    update_item(matches[0], updates)
    json_build(id=item_id)


def delete(flags):
    project = require_flag(flags, "project")
    item_id = require_flag(flags, "id")

    d = require_project(project)
    issue_dir = d / "issues"

    matches = sorted(issue_dir.glob(f"{item_id}-*.md")) if issue_dir.is_dir() else []
    if not matches:
        print(f"Issue not found: {item_id}", file=sys.stderr)
        sys.exit(1)

    matches[0].unlink()
    json_build(id=item_id, deleted="true")


def main():
    if len(sys.argv) < 2:
        print("Usage: issue.py <create|get|list|update|delete> [flags]", file=sys.stderr)
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
        print("Usage: issue.py <create|get|list|update|delete> [flags]", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
