"""
Filesystem and interview-specific assertions.

Python reimplementation of tests/harness/lib/assertions.ts.
"""

import json
import os
import re
from pathlib import Path

# ── Filesystem assertions ────────────────────────────────────────────


def file_exists(base_dir: str, filename: str) -> bool:
    """Return True if the file exists under base_dir."""
    return Path(base_dir, filename).exists()


def file_contains(base_dir: str, filename: str, text: str) -> bool:
    """Return True if the file exists and contains the given text."""
    full_path = Path(base_dir, filename)
    if not full_path.exists():
        return False
    return text in full_path.read_text(encoding="utf-8")


def file_matches(base_dir: str, filename: str, pattern) -> bool:
    """Return True if the file exists and its content matches the compiled regex."""
    full_path = Path(base_dir, filename)
    if not full_path.exists():
        return False
    return bool(pattern.search(full_path.read_text(encoding="utf-8")))


def list_files(base_dir: str, subdir: str) -> list:
    """Return a sorted list of filenames (not dirs) in base_dir/subdir."""
    full_path = Path(base_dir, subdir)
    if not full_path.exists():
        return []
    return sorted(
        entry.name for entry in full_path.iterdir() if entry.is_file()
    )


# ── Interview-specific assertions ─────────────────────────────────────

# Timestamp filename pattern: YYYY-MM-DD-HH-MM-SS-slug.md
_TIMESTAMP_FILENAME = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-.+\.md$")


def all_files_match_timestamp_pattern(base_dir: str, subdir: str) -> bool:
    """Return True if all files in the directory match the timestamp naming convention."""
    files = list_files(base_dir, subdir)
    return len(files) > 0 and all(_TIMESTAMP_FILENAME.match(f) for f in files)


def has_valid_frontmatter(base_dir: str, filename: str, required_fields: list) -> bool:
    """Return True if the file has YAML frontmatter containing all required fields."""
    full_path = Path(base_dir, filename)
    content = full_path.read_text(encoding="utf-8")
    match = re.search(r"^---\n([\s\S]*?)\n---", content)
    if not match:
        return False
    frontmatter = match.group(1)
    return all(
        re.search(rf"^{re.escape(field)}:", frontmatter, re.MULTILINE)
        for field in required_fields
    )


def parse_test_log(base_dir: str, filename: str) -> list:
    """Parse a JSONL test log and return a list of event dicts."""
    full_path = Path(base_dir, filename)
    content = full_path.read_text(encoding="utf-8").strip()
    return [json.loads(line) for line in content.splitlines() if line.strip()]


def specialists_invoked(events: list) -> list:
    """Return unique specialist names in order of first appearance."""
    seen = []
    seen_set = set()
    for e in events:
        if e.get("event") == "specialist_invoked":
            name = e.get("specialist")
            if name and name not in seen_set:
                seen.append(name)
                seen_set.add(name)
    return seen


def exchange_count(events: list) -> int:
    """Count question_asked events."""
    return sum(1 for e in events if e.get("event") == "question_asked")


def all_questions_answered(events: list) -> bool:
    """Return True if every question_asked has a matching answer_received."""
    questions = sum(1 for e in events if e.get("event") == "question_asked")
    answers = sum(1 for e in events if e.get("event") == "answer_received")
    return questions == answers


def all_answers_analyzed(events: list) -> bool:
    """Return True if every answer_received has a matching analysis_written."""
    answers = sum(1 for e in events if e.get("event") == "answer_received")
    analyses = sum(1 for e in events if e.get("event") == "analysis_written")
    return answers == analyses


# ── Required frontmatter field lists ─────────────────────────────────

TRANSCRIPT_FIELDS = [
    "id",
    "title",
    "type",
    "created",
    "modified",
    "author",
    "summary",
    "project",
    "session",
    "specialist",
]

ANALYSIS_FIELDS = [
    "id",
    "title",
    "type",
    "created",
    "modified",
    "author",
    "summary",
    "related",
    "project",
    "session",
    "specialist",
]
