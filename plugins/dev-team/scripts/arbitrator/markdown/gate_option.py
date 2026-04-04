#!/usr/bin/env python3
"""Gate-option resource for markdown arbitrator."""
import json
import sys
from _lib import (
    parse_flags, require_flag, require_session,
    json_output,
)


def add(flags):
    message_id = require_flag(flags, "message")
    option_text = require_flag(flags, "option_text")
    is_default = require_flag(flags, "is_default")
    sort_order = require_flag(flags, "sort_order")

    # Composite ID format: <session_id>:message:<seq>
    parts = message_id.split(":message:", 1)
    session_id = parts[0]
    msg_seq = parts[1] if len(parts) == 2 else ""

    d = require_session(session_id)
    gate_dir = d / "gate-options"
    gate_dir.mkdir(parents=True, exist_ok=True)

    file = gate_dir / f"{msg_seq}-option-{sort_order}.json"
    entry_id = f"{message_id}:option:{sort_order}"

    data = {
        "id": entry_id,
        "message_id": message_id,
        "option_text": option_text,
        "is_default": is_default,
        "sort_order": sort_order,
    }
    file.write_text(json.dumps(data, ensure_ascii=False))
    print(file.read_text())


def list_all(flags):
    message_id = require_flag(flags, "message")

    # Composite ID format: <session_id>:message:<seq>
    parts = message_id.split(":message:", 1)
    session_id = parts[0]
    msg_seq = parts[1] if len(parts) == 2 else ""

    d = require_session(session_id)
    gate_dir = d / "gate-options"

    if not gate_dir.is_dir():
        print("[]")
        return

    results = []
    for f in sorted(gate_dir.glob(f"{msg_seq}-option-*.json")):
        if f.is_file():
            results.append(json.loads(f.read_text()))

    json_output(results)


def main():
    if len(sys.argv) < 2:
        print("Usage: gate_option.py <add|list> [flags]", file=sys.stderr)
        sys.exit(1)
    action = sys.argv[1]
    flags = parse_flags(sys.argv[2:])

    actions = {
        "add": add,
        "list": list_all,
    }
    if action not in actions:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)
    actions[action](flags)


if __name__ == "__main__":
    main()
