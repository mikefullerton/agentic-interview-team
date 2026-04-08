"""Shared helpers for the team-pipeline storage-provider markdown backend."""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from random import randint

SESSION_BASE = Path(
    os.environ.get(
        "TEAM_PIPELINE_SESSION_BASE",
        os.path.expanduser("~/.team-pipeline/sessions"),
    )
)


# ---------------------------------------------------------------------------
# Date/time helpers
# ---------------------------------------------------------------------------

def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# String helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:40]


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def json_build(**kwargs) -> None:
    """Build a JSON object from kwargs and print it to stdout."""
    print(json.dumps(kwargs, ensure_ascii=False))


def json_output(obj) -> None:
    """Print a JSON object to stdout."""
    print(json.dumps(obj, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Flag parsing
# ---------------------------------------------------------------------------

def parse_flags(argv: list) -> dict:
    """Parse --flag value pairs from argv into a dict."""
    flags = {}
    flag_map = {
        "--session": "session",
        "--specialist": "specialist",
        "--state": "state",
        "--changed-by": "changed_by",
        "--content": "content",
        "--category": "category",
        "--detail": "detail",
        "--playbook": "playbook",
        "--team-lead": "team_lead",
        "--user": "user",
        "--machine": "machine",
        "--result": "result",
        "--finding": "finding",
        "--message": "message",
        "--artifact": "artifact",
        "--interpretation": "interpretation",
        "--option-text": "option_text",
        "--is-default": "is_default",
        "--sort-order": "sort_order",
        "--reason": "reason",
        "--team": "team",
        "--iteration": "iteration",
        "--verifier-feedback": "verifier_feedback",
        "--add-consulting-annotation": "add_consulting_annotation",
        "--description": "description",
        "--path": "path",
        "--title": "title",
        "--severity": "severity",
        "--status": "status",
        "--type": "type",
        "--name": "name",
    }
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in flag_map and i + 1 < len(argv):
            flags[flag_map[arg]] = argv[i + 1]
            i += 2
        else:
            i += 1
    return flags


def require_flag(flags: dict, name: str) -> str:
    """Require a flag is present and non-empty."""
    val = flags.get(name, "")
    if not val:
        print(f"Missing required flag: --{name.replace('_', '-')}", file=sys.stderr)
        sys.exit(1)
    return val


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def new_session_id() -> str:
    """Generate a human-readable, sortable, collision-resistant session ID."""
    now = datetime.now(timezone.utc)
    return f"{now.strftime('%Y%m%d-%H%M%S')}-{randint(0, 65535):04x}"


def session_dir(session_id: str) -> Path:
    return SESSION_BASE / session_id


def require_session(session_id: str) -> Path:
    d = session_dir(session_id)
    if not d.is_dir():
        print(f"Session not found: {session_id}", file=sys.stderr)
        sys.exit(1)
    return d


def next_seq(directory: Path) -> str:
    """Get next zero-padded sequence number for a directory."""
    directory.mkdir(parents=True, exist_ok=True)
    count = sum(
        1
        for f in directory.iterdir()
        if f.suffix in (".json", ".jsonl") and f.is_file()
    )
    return f"{count + 1:04d}"
