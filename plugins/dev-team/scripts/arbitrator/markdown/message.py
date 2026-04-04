#!/usr/bin/env python3
"""Message resource for markdown arbitrator."""
import json
import sys
from _lib import (
    parse_flags, require_flag, require_session,
    next_seq, now_iso, json_output,
)


def send(flags):
    session_id = require_flag(flags, "session")
    type_ = require_flag(flags, "type")
    changed_by = require_flag(flags, "changed_by")
    content = require_flag(flags, "content")
    specialist = flags.get("specialist", "")
    category = flags.get("category", "")
    severity = flags.get("severity", "")

    d = require_session(session_id)
    msg_dir = d / "messages"
    seq = next_seq(msg_dir)
    timestamp = now_iso()
    ts_slug = timestamp.replace(":", "-")
    file = msg_dir / f"{seq}-{ts_slug}-{type_}.json"

    entry_id = f"{session_id}:message:{seq}"
    data = {
        "id": entry_id,
        "session_id": session_id,
        "creation_date": timestamp,
        "type": type_,
        "changed_by": changed_by,
        "content": content,
        "specialist": specialist,
        "category": category,
        "severity": severity,
    }
    file.write_text(json.dumps(data, ensure_ascii=False))
    print(file.read_text())


def list_all(flags):
    session_id = require_flag(flags, "session")

    d = require_session(session_id)
    msg_dir = d / "messages"

    if not msg_dir.is_dir():
        print("[]")
        return

    type_filter = flags.get("type", "")
    results = []
    for f in sorted(msg_dir.glob("*.json")):
        if not f.is_file():
            continue
        data = json.loads(f.read_text())
        if type_filter and data.get("type") != type_filter:
            continue
        results.append(data)

    json_output(results)


def get(flags):
    message_id = require_flag(flags, "message")

    # Composite ID format: <session_id>:message:<seq>
    session_id = message_id.split(":message:")[0]
    seq = message_id.split(":message:")[-1]

    d = require_session(session_id)
    msg_dir = d / "messages"

    if not msg_dir.is_dir():
        print(f"No messages found for session: {session_id}", file=sys.stderr)
        sys.exit(1)

    matches = sorted(msg_dir.glob(f"{seq}-*.json"))
    if not matches:
        print(f"Message not found: {message_id}", file=sys.stderr)
        sys.exit(1)

    print(matches[0].read_text())


def main():
    if len(sys.argv) < 2:
        print("Usage: message.py <send|list|get> [flags]", file=sys.stderr)
        sys.exit(1)
    action = sys.argv[1]
    flags = parse_flags(sys.argv[2:])

    actions = {
        "send": send,
        "list": list_all,
        "get": get,
    }
    if action not in actions:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
