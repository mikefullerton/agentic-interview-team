"""Playbook loader — happy path and error paths."""
from __future__ import annotations

from pathlib import Path

import pytest

from services.conductor.playbook import load_playbook
from services.conductor.playbook.types import TeamPlaybook


def test_load_existing_playbook(playbooks_dir: Path):
    playbook = load_playbook(playbooks_dir / "name_a_puppy.py")
    assert isinstance(playbook, TeamPlaybook)
    assert playbook.name == "name-a-puppy"
    assert playbook.initial_state in {s.name for s in playbook.states}


def test_load_cross_team_playbooks(playbooks_dir: Path):
    coach = load_playbook(playbooks_dir / "pet_coach.py")
    assert coach.name == "pet-coach"
    assert "pet_coach.suggest_theme" in coach.request_handlers


def test_missing_file_raises_file_not_found(tmp_path):
    missing = tmp_path / "does_not_exist.py"
    with pytest.raises(FileNotFoundError) as exc_info:
        load_playbook(missing)
    assert "does_not_exist.py" in str(exc_info.value)


def test_module_without_playbook_export_raises(tmp_path):
    bad = tmp_path / "no_export.py"
    bad.write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(TypeError) as exc_info:
        load_playbook(bad)
    assert "PLAYBOOK" in str(exc_info.value)


def test_playbook_export_wrong_type_raises(tmp_path):
    bad = tmp_path / "wrong_type.py"
    bad.write_text("PLAYBOOK = 'not a TeamPlaybook'\n", encoding="utf-8")
    with pytest.raises(TypeError) as exc_info:
        load_playbook(bad)
    assert "TeamPlaybook" in str(exc_info.value)


def test_syntax_error_propagates(tmp_path):
    bad = tmp_path / "syntax.py"
    bad.write_text("def broken(:\n  pass\n", encoding="utf-8")
    with pytest.raises(SyntaxError):
        load_playbook(bad)
