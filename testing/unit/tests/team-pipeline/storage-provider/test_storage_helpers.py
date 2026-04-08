"""Tests for team-pipeline storage helpers."""
import os
import sys
from pathlib import Path

import pytest

# Add the storage-provider markdown directory to sys.path
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
SP_DIR = REPO_ROOT / "plugins" / "team-pipeline" / "scripts" / "storage-provider" / "markdown"
sys.path.insert(0, str(SP_DIR))

from storage_helpers import (
    today_iso,
    now_iso,
    slugify,
    json_build,
    json_output,
    parse_flags,
    require_flag,
    new_session_id,
    session_dir,
    next_seq,
    SESSION_BASE,
)


def test_session_base_uses_env(tmp_path, monkeypatch):
    monkeypatch.setenv("TEAM_PIPELINE_SESSION_BASE", str(tmp_path / "custom"))
    # Reimport to pick up env change
    import importlib
    import storage_helpers
    importlib.reload(storage_helpers)
    assert storage_helpers.SESSION_BASE == tmp_path / "custom"


def test_slugify_basic():
    assert slugify("Hello World!") == "hello-world"


def test_slugify_strips_leading_trailing_hyphens():
    assert slugify("--test--") == "test"


def test_slugify_truncates_at_40():
    assert len(slugify("a" * 100)) <= 40


def test_today_iso_format():
    result = today_iso()
    assert len(result) == 10  # YYYY-MM-DD
    assert result[4] == "-" and result[7] == "-"


def test_now_iso_format():
    result = now_iso()
    assert "T" in result and result.endswith("Z")


def test_parse_flags_extracts_pairs():
    flags = parse_flags(["--session", "abc", "--specialist", "security"])
    assert flags["session"] == "abc"
    assert flags["specialist"] == "security"


def test_parse_flags_skips_unknown():
    flags = parse_flags(["--unknown", "val", "--session", "abc"])
    assert "unknown" not in flags
    assert flags["session"] == "abc"


def test_require_flag_returns_value():
    assert require_flag({"session": "abc"}, "session") == "abc"


def test_require_flag_exits_on_missing():
    with pytest.raises(SystemExit):
        require_flag({}, "session")


def test_new_session_id_format():
    sid = new_session_id()
    parts = sid.split("-")
    assert len(parts) == 3  # YYYYMMDD-HHMMSS-XXXX
    assert len(parts[0]) == 8
    assert len(parts[1]) == 6
    assert len(parts[2]) == 4


def test_session_dir_uses_base(tmp_path, monkeypatch):
    monkeypatch.setenv("TEAM_PIPELINE_SESSION_BASE", str(tmp_path))
    import importlib
    import storage_helpers
    importlib.reload(storage_helpers)
    d = storage_helpers.session_dir("test-123")
    assert d == tmp_path / "test-123"


def test_next_seq_starts_at_0001(tmp_path):
    seq = next_seq(tmp_path / "subdir")
    assert seq == "0001"


def test_next_seq_increments(tmp_path):
    d = tmp_path / "subdir"
    d.mkdir()
    (d / "0001.json").write_text("{}")
    seq = next_seq(d)
    assert seq == "0002"
