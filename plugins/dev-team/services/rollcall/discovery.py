"""Walk a `teams/` tree and yield every pingable role.

Role kinds (per design doc):
    team-lead          — teams/<team>/team-leads/<lead>.md
    specialty-worker   — teams/<team>/specialists/<sp>/specialities/<sty>.md
    specialty-verifier — paired with the worker above

Standalone specialists are organizational containers (no prompt of their
own in v1), so discovery does not emit a bare `specialist` kind. The
kind stays in the Literal as a forward-compatible slot.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


RoleKind = Literal[
    "team-lead", "specialist", "specialty-worker", "specialty-verifier"
]


@dataclass(frozen=True)
class RoleRef:
    team: str
    kind: RoleKind
    name: str
    path: Path


def _discover_team_leads(team_root: Path, team: str) -> list[RoleRef]:
    leads_dir = team_root / "team-leads"
    if not leads_dir.is_dir():
        return []
    out: list[RoleRef] = []
    for md in sorted(leads_dir.iterdir()):
        if md.suffix != ".md" or md.name == "index.md":
            continue
        out.append(
            RoleRef(team=team, kind="team-lead", name=md.stem, path=md)
        )
    return out


def _discover_specialty_roles(team_root: Path, team: str) -> list[RoleRef]:
    specialists_dir = team_root / "specialists"
    if not specialists_dir.is_dir():
        return []
    out: list[RoleRef] = []
    for sp_dir in sorted(specialists_dir.iterdir()):
        if not sp_dir.is_dir():
            continue
        for candidate in ("specialities", "specialties"):
            spec_dir = sp_dir / candidate
            if not spec_dir.is_dir():
                continue
            for md in sorted(spec_dir.iterdir()):
                if md.suffix != ".md" or md.name == "index.md":
                    continue
                role_name = f"{sp_dir.name}.{md.stem}"
                out.append(RoleRef(
                    team=team, kind="specialty-worker",
                    name=role_name, path=md,
                ))
                out.append(RoleRef(
                    team=team, kind="specialty-verifier",
                    name=role_name, path=md,
                ))
            break
    return out


def discover_team(team_root: Path) -> list[RoleRef]:
    """Return every role in one team directory."""
    team_root = team_root.resolve()
    team = team_root.name
    return _discover_team_leads(team_root, team) + _discover_specialty_roles(
        team_root, team
    )


def discover_teams(teams_root: Path) -> list[RoleRef]:
    """Discover roles across every team directory under `teams_root`."""
    teams_root = teams_root.resolve()
    out: list[RoleRef] = []
    for entry in sorted(teams_root.iterdir()):
        if not entry.is_dir():
            continue
        out.extend(discover_team(entry))
    return out
