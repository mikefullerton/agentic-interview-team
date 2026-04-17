"""Arbitrator resource dataclasses.

One class per resource from spec §6.1. All rows carry (session_id, team_id)
except `request` which has (from_team, to_team).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID


class SessionStatus(str, Enum):
    OPEN = "open"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class StateStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class RequestStatus(str, Enum):
    PENDING = "pending"
    IN_FLIGHT = "in_flight"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class NodeKind(str, Enum):
    COMPOUND = "compound"
    PRIMITIVE = "primitive"


class NodeStateEventType(str, Enum):
    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SUPERSEDED = "superseded"


class BodyFormat(str, Enum):
    MARKDOWN = "markdown"
    PLAIN = "plain"
    JSON = "json"


@dataclass
class Session:
    session_id: UUID
    initial_team_id: str
    status: SessionStatus
    started_at: datetime
    ended_at: datetime | None = None
    metadata_json: dict[str, Any] = field(default_factory=dict)


@dataclass
class StateNode:
    node_id: str
    session_id: UUID
    team_id: str
    parent_node_id: str | None
    state_name: str
    status: StateStatus
    entered_at: datetime
    exited_at: datetime | None = None


@dataclass
class Message:
    message_id: str
    session_id: UUID
    team_id: str
    direction: str  # "in" (user→lead) or "out" (lead→user)
    type: str  # "question" | "answer" | "notification"
    body: str
    created_at: datetime


@dataclass
class Gate:
    gate_id: str
    session_id: UUID
    team_id: str
    category: str
    options_json: list[str]
    verdict: str | None
    created_at: datetime
    resolved_at: datetime | None = None


@dataclass
class Result:
    result_id: str
    session_id: UUID
    team_id: str
    specialist_id: str
    passed: bool
    summary_json: dict[str, Any]
    created_at: datetime


@dataclass
class Finding:
    finding_id: str
    result_id: str
    kind: str
    severity: str
    body: str
    source_artifact: str | None = None


@dataclass
class Event:
    event_id: str
    session_id: UUID
    team_id: str | None
    agent_id: str | None
    dispatch_id: str | None
    sequence: int
    kind: str
    payload_json: dict[str, Any]
    emitted_at: datetime


@dataclass
class Task:
    task_id: str
    session_id: UUID
    team_id: str
    kind: str
    payload_json: dict[str, Any]
    status: TaskStatus
    enqueued_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result_json: dict[str, Any] | None = None


@dataclass
class Request:
    request_id: str
    session_id: UUID
    from_team: str
    to_team: str
    kind: str
    input_json: dict[str, Any]
    status: RequestStatus
    response_json: dict[str, Any] | None
    parent_request_id: str | None
    enqueued_at: datetime
    in_flight_at: datetime | None
    completed_at: datetime | None
    timeout_at: datetime


# ---------------------------------------------------------------------------
# Roadmap graph — project-scoped, survives across sessions.
# See docs/planning/2026-04-17-atp-roadmap-design.md.
# ---------------------------------------------------------------------------


@dataclass
class Roadmap:
    roadmap_id: str
    title: str
    creation_date: datetime
    modification_date: datetime


@dataclass
class PlanNode:
    node_id: str
    roadmap_id: str
    parent_id: str | None
    position: float
    node_kind: NodeKind
    title: str
    creation_date: datetime
    modification_date: datetime
    specialist: str | None = None
    speciality: str | None = None


@dataclass
class NodeDependency:
    dependency_id: int
    node_id: str             # dependent
    depends_on_id: str       # prerequisite
    creation_date: datetime


@dataclass
class NodeStateEvent:
    event_id: int
    node_id: str
    event_type: NodeStateEventType
    actor: str
    event_date: datetime
    session_id: UUID | None = None


@dataclass
class Body:
    owner_type: str          # plan_node | message | finding | ...
    owner_id: str
    body_format: BodyFormat
    body_text: str
    modification_date: datetime
