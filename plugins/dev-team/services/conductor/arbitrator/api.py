"""Arbitrator — single API facade over the shared DB.

See spec §5.2. Every component reads and writes through this object.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator
from uuid import UUID

from .backends.base import Storage
from .models import (
    Event,
    Finding,
    Gate,
    Message,
    Request,
    RequestStatus,
    Result,
    Session,
    SessionStatus,
    StateNode,
    StateStatus,
    Task,
    TaskStatus,
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Arbitrator:
    """Async facade over a `Storage` backend.

    All resource rows carry `(session_id, team_id)` as part of their uniqueness
    (except `request`, which has `from_team`/`to_team`).
    """

    def __init__(self, storage: Storage):
        self._storage = storage
        # Sequence counter for events, keyed per session.
        self._event_seq: dict[str, int] = {}
        # Registered request kinds: {kind: (input_schema, response_schema, timeout_s)}
        self._request_kinds: dict[str, tuple[dict, dict, int]] = {}
        # Registered request handlers: {(team_id, kind): handler_state_node}
        self._request_handlers: dict[tuple[str, str], str] = {}

    async def start(self) -> None:
        await self._storage.connect()

    async def close(self) -> None:
        await self._storage.close()

    # ---- Sessions ---------------------------------------------------------

    async def open_session(
        self,
        session_id: UUID,
        initial_team_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        existing = await self._storage.fetch_one(
            "session", {"session_id": str(session_id)}
        )
        if existing:
            return Session(
                session_id=UUID(existing["session_id"]),
                initial_team_id=existing["initial_team_id"],
                status=SessionStatus(existing["status"]),
                started_at=datetime.fromisoformat(existing["started_at"]),
                ended_at=(
                    datetime.fromisoformat(existing["ended_at"])
                    if existing["ended_at"]
                    else None
                ),
                metadata_json=json.loads(existing["metadata_json"]),
            )
        now = _utcnow_iso()
        row = {
            "session_id": str(session_id),
            "initial_team_id": initial_team_id,
            "status": SessionStatus.OPEN.value,
            "started_at": now,
            "ended_at": None,
            "metadata_json": json.dumps(metadata or {}),
        }
        await self._storage.insert("session", row)
        return Session(
            session_id=session_id,
            initial_team_id=initial_team_id,
            status=SessionStatus.OPEN,
            started_at=datetime.fromisoformat(now),
            metadata_json=metadata or {},
        )

    async def close_session(
        self, session_id: UUID, status: SessionStatus
    ) -> None:
        await self._storage.update(
            "session",
            {"session_id": str(session_id)},
            {"status": status.value, "ended_at": _utcnow_iso()},
        )

    # ---- State tree -------------------------------------------------------

    async def push_state(
        self,
        session_id: UUID,
        team_id: str,
        state_name: str,
        parent_node_id: str | None,
    ) -> StateNode:
        node_id = _new_id("state")
        now = _utcnow_iso()
        await self._storage.insert(
            "state",
            {
                "node_id": node_id,
                "session_id": str(session_id),
                "team_id": team_id,
                "parent_node_id": parent_node_id,
                "state_name": state_name,
                "status": StateStatus.ACTIVE.value,
                "entered_at": now,
                "exited_at": None,
            },
        )
        return StateNode(
            node_id=node_id,
            session_id=session_id,
            team_id=team_id,
            parent_node_id=parent_node_id,
            state_name=state_name,
            status=StateStatus.ACTIVE,
            entered_at=datetime.fromisoformat(now),
        )

    async def pop_state(
        self, node_id: str, status: StateStatus = StateStatus.COMPLETED
    ) -> None:
        await self._storage.update(
            "state",
            {"node_id": node_id},
            {"status": status.value, "exited_at": _utcnow_iso()},
        )

    async def active_state_nodes(
        self, session_id: UUID
    ) -> list[StateNode]:
        rows = await self._storage.fetch_all(
            "state",
            where={
                "session_id": str(session_id),
                "status": StateStatus.ACTIVE.value,
            },
            order_by="entered_at",
        )
        return [_row_to_state_node(r) for r in rows]

    # ---- Messages ---------------------------------------------------------

    async def create_message(
        self,
        session_id: UUID,
        team_id: str,
        direction: str,
        type: str,
        body: str,
    ) -> Message:
        message_id = _new_id("msg")
        now = _utcnow_iso()
        await self._storage.insert(
            "message",
            {
                "message_id": message_id,
                "session_id": str(session_id),
                "team_id": team_id,
                "direction": direction,
                "type": type,
                "body": body,
                "created_at": now,
            },
        )
        return Message(
            message_id=message_id,
            session_id=session_id,
            team_id=team_id,
            direction=direction,
            type=type,
            body=body,
            created_at=datetime.fromisoformat(now),
        )

    async def list_messages(
        self, session_id: UUID, team_id: str | None = None
    ) -> list[Message]:
        where: dict[str, Any] = {"session_id": str(session_id)}
        if team_id is not None:
            where["team_id"] = team_id
        rows = await self._storage.fetch_all(
            "message", where=where, order_by="created_at"
        )
        return [_row_to_message(r) for r in rows]

    # ---- Gates ------------------------------------------------------------

    async def create_gate(
        self,
        session_id: UUID,
        team_id: str,
        category: str,
        options: list[str],
    ) -> Gate:
        gate_id = _new_id("gate")
        now = _utcnow_iso()
        await self._storage.insert(
            "gate",
            {
                "gate_id": gate_id,
                "session_id": str(session_id),
                "team_id": team_id,
                "category": category,
                "options_json": json.dumps(options),
                "verdict": None,
                "created_at": now,
                "resolved_at": None,
            },
        )
        return Gate(
            gate_id=gate_id,
            session_id=session_id,
            team_id=team_id,
            category=category,
            options_json=options,
            verdict=None,
            created_at=datetime.fromisoformat(now),
        )

    async def resolve_gate(self, gate_id: str, verdict: str) -> None:
        await self._storage.update(
            "gate",
            {"gate_id": gate_id},
            {"verdict": verdict, "resolved_at": _utcnow_iso()},
        )

    # ---- Results / Findings ----------------------------------------------

    async def create_result(
        self,
        session_id: UUID,
        team_id: str,
        specialist_id: str,
        passed: bool,
        summary: dict[str, Any],
    ) -> Result:
        result_id = _new_id("res")
        now = _utcnow_iso()
        await self._storage.insert(
            "result",
            {
                "result_id": result_id,
                "session_id": str(session_id),
                "team_id": team_id,
                "specialist_id": specialist_id,
                "passed": 1 if passed else 0,
                "summary_json": json.dumps(summary),
                "created_at": now,
            },
        )
        return Result(
            result_id=result_id,
            session_id=session_id,
            team_id=team_id,
            specialist_id=specialist_id,
            passed=passed,
            summary_json=summary,
            created_at=datetime.fromisoformat(now),
        )

    async def list_results(
        self, session_id: UUID, team_id: str | None = None
    ) -> list[Result]:
        where: dict[str, Any] = {"session_id": str(session_id)}
        if team_id is not None:
            where["team_id"] = team_id
        rows = await self._storage.fetch_all(
            "result", where=where, order_by="created_at"
        )
        return [_row_to_result(r) for r in rows]

    async def create_finding(
        self,
        result_id: str,
        kind: str,
        severity: str,
        body: str,
        source_artifact: str | None = None,
    ) -> Finding:
        finding_id = _new_id("find")
        await self._storage.insert(
            "finding",
            {
                "finding_id": finding_id,
                "result_id": result_id,
                "kind": kind,
                "severity": severity,
                "body": body,
                "source_artifact": source_artifact,
            },
        )
        return Finding(
            finding_id=finding_id,
            result_id=result_id,
            kind=kind,
            severity=severity,
            body=body,
            source_artifact=source_artifact,
        )

    # ---- Events -----------------------------------------------------------

    async def emit_event(
        self,
        session_id: UUID,
        team_id: str | None,
        kind: str,
        payload: dict[str, Any],
        agent_id: str | None = None,
        dispatch_id: str | None = None,
    ) -> Event:
        key = str(session_id)
        self._event_seq[key] = self._event_seq.get(key, 0) + 1
        seq = self._event_seq[key]
        event_id = _new_id("evt")
        now = _utcnow_iso()
        await self._storage.insert(
            "event",
            {
                "event_id": event_id,
                "session_id": key,
                "team_id": team_id,
                "agent_id": agent_id,
                "dispatch_id": dispatch_id,
                "sequence": seq,
                "kind": kind,
                "payload_json": json.dumps(payload),
                "emitted_at": now,
            },
        )
        return Event(
            event_id=event_id,
            session_id=session_id,
            team_id=team_id,
            agent_id=agent_id,
            dispatch_id=dispatch_id,
            sequence=seq,
            kind=kind,
            payload_json=payload,
            emitted_at=datetime.fromisoformat(now),
        )

    async def list_events(
        self, session_id: UUID, since_sequence: int = 0
    ) -> list[Event]:
        rows = await self._storage.fetch_all(
            "event",
            where={"session_id": str(session_id)},
            order_by="sequence",
        )
        return [
            _row_to_event(r) for r in rows if int(r["sequence"]) > since_sequence
        ]

    # ---- Tasks (work queue) ----------------------------------------------

    async def enqueue_task(
        self,
        session_id: UUID,
        team_id: str,
        kind: str,
        payload: dict[str, Any],
    ) -> Task:
        task_id = _new_id("task")
        now = _utcnow_iso()
        await self._storage.insert(
            "task",
            {
                "task_id": task_id,
                "session_id": str(session_id),
                "team_id": team_id,
                "kind": kind,
                "payload_json": json.dumps(payload),
                "status": TaskStatus.PENDING.value,
                "enqueued_at": now,
                "started_at": None,
                "completed_at": None,
                "result_json": None,
            },
        )
        return Task(
            task_id=task_id,
            session_id=session_id,
            team_id=team_id,
            kind=kind,
            payload_json=payload,
            status=TaskStatus.PENDING,
            enqueued_at=datetime.fromisoformat(now),
        )

    async def next_task(self, session_id: UUID) -> Task | None:
        rows = await self._storage.fetch_all(
            "task",
            where={
                "session_id": str(session_id),
                "status": TaskStatus.PENDING.value,
            },
            order_by="enqueued_at",
            limit=1,
        )
        if not rows:
            return None
        row = rows[0]
        await self._storage.update(
            "task",
            {"task_id": row["task_id"]},
            {
                "status": TaskStatus.IN_PROGRESS.value,
                "started_at": _utcnow_iso(),
            },
        )
        return _row_to_task(row, status_override=TaskStatus.IN_PROGRESS)

    async def complete_task(
        self,
        task_id: str,
        result: dict[str, Any] | None = None,
        status: TaskStatus = TaskStatus.COMPLETED,
    ) -> None:
        await self._storage.update(
            "task",
            {"task_id": task_id},
            {
                "status": status.value,
                "completed_at": _utcnow_iso(),
                "result_json": json.dumps(result) if result is not None else None,
            },
        )

    # ---- Requests (inter-team) -------------------------------------------

    def register_request_kind(
        self,
        kind: str,
        input_schema: dict,
        response_schema: dict,
        default_timeout_seconds: int = 300,
    ) -> None:
        self._request_kinds[kind] = (
            input_schema,
            response_schema,
            default_timeout_seconds,
        )

    def register_request_handler(
        self, team_id: str, kind: str, handler_state_node: str
    ) -> None:
        self._request_handlers[(team_id, kind)] = handler_state_node

    async def create_request(
        self,
        session_id: UUID,
        from_team: str,
        to_team: str,
        kind: str,
        input_data: dict[str, Any],
        parent_request_id: str | None = None,
        timeout_seconds: int | None = None,
    ) -> Request:
        if kind not in self._request_kinds:
            raise ValueError(f"Unregistered request kind: {kind}")
        if (to_team, kind) not in self._request_handlers:
            raise ValueError(
                f"No handler registered for {kind!r} on team {to_team!r}"
            )
        _, _, default_timeout = self._request_kinds[kind]
        timeout = timeout_seconds or default_timeout
        now = datetime.now(timezone.utc)
        request_id = _new_id("req")
        await self._storage.insert(
            "request",
            {
                "request_id": request_id,
                "session_id": str(session_id),
                "from_team": from_team,
                "to_team": to_team,
                "kind": kind,
                "input_json": json.dumps(input_data),
                "status": RequestStatus.PENDING.value,
                "response_json": None,
                "parent_request_id": parent_request_id,
                "enqueued_at": now.isoformat(),
                "in_flight_at": None,
                "completed_at": None,
                "timeout_at": (now + timedelta(seconds=timeout)).isoformat(),
            },
        )
        return Request(
            request_id=request_id,
            session_id=session_id,
            from_team=from_team,
            to_team=to_team,
            kind=kind,
            input_json=input_data,
            status=RequestStatus.PENDING,
            response_json=None,
            parent_request_id=parent_request_id,
            enqueued_at=now,
            in_flight_at=None,
            completed_at=None,
            timeout_at=now + timedelta(seconds=timeout),
        )

    async def next_ready_request(
        self, session_id: UUID
    ) -> Request | None:
        """Return the next request that is ready to be handled.

        Enforces the serial queue from §7.4: at most one root-level request
        (`parent_request_id is NULL`) in `in_flight` per session.
        Child requests (`parent_request_id` non-null) bypass the queue.
        """
        # Any child request pending? They bypass the queue.
        child_rows = await self._storage.fetch_all(
            "request",
            where={
                "session_id": str(session_id),
                "status": RequestStatus.PENDING.value,
            },
            order_by="enqueued_at",
        )
        for row in child_rows:
            if row["parent_request_id"]:
                await self._mark_request_in_flight(row["request_id"])
                return _row_to_request(row, RequestStatus.IN_FLIGHT)
        # Otherwise root requests — only one at a time.
        in_flight = [
            r for r in child_rows if False
        ]  # placeholder, replaced below
        in_flight_rows = await self._storage.fetch_all(
            "request",
            where={
                "session_id": str(session_id),
                "status": RequestStatus.IN_FLIGHT.value,
            },
        )
        if any(r["parent_request_id"] is None for r in in_flight_rows):
            return None  # root already in flight
        for row in child_rows:
            if row["parent_request_id"] is None:
                await self._mark_request_in_flight(row["request_id"])
                return _row_to_request(row, RequestStatus.IN_FLIGHT)
        return None

    async def _mark_request_in_flight(self, request_id: str) -> None:
        await self._storage.update(
            "request",
            {"request_id": request_id},
            {
                "status": RequestStatus.IN_FLIGHT.value,
                "in_flight_at": _utcnow_iso(),
            },
        )

    async def complete_request(
        self,
        request_id: str,
        response: dict[str, Any],
        status: RequestStatus = RequestStatus.COMPLETED,
    ) -> None:
        await self._storage.update(
            "request",
            {"request_id": request_id},
            {
                "status": status.value,
                "response_json": json.dumps(response),
                "completed_at": _utcnow_iso(),
            },
        )

    async def get_request(self, request_id: str) -> Request | None:
        row = await self._storage.fetch_one(
            "request", {"request_id": request_id}
        )
        return _row_to_request(row, None) if row else None


# ---------------------------------------------------------------------------
# Row → dataclass helpers
# ---------------------------------------------------------------------------


def _row_to_state_node(row: dict[str, Any]) -> StateNode:
    return StateNode(
        node_id=row["node_id"],
        session_id=UUID(row["session_id"]),
        team_id=row["team_id"],
        parent_node_id=row["parent_node_id"],
        state_name=row["state_name"],
        status=StateStatus(row["status"]),
        entered_at=datetime.fromisoformat(row["entered_at"]),
        exited_at=(
            datetime.fromisoformat(row["exited_at"]) if row["exited_at"] else None
        ),
    )


def _row_to_message(row: dict[str, Any]) -> Message:
    return Message(
        message_id=row["message_id"],
        session_id=UUID(row["session_id"]),
        team_id=row["team_id"],
        direction=row["direction"],
        type=row["type"],
        body=row["body"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _row_to_result(row: dict[str, Any]) -> Result:
    return Result(
        result_id=row["result_id"],
        session_id=UUID(row["session_id"]),
        team_id=row["team_id"],
        specialist_id=row["specialist_id"],
        passed=bool(row["passed"]),
        summary_json=json.loads(row["summary_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _row_to_event(row: dict[str, Any]) -> Event:
    return Event(
        event_id=row["event_id"],
        session_id=UUID(row["session_id"]),
        team_id=row["team_id"],
        agent_id=row["agent_id"],
        dispatch_id=row["dispatch_id"],
        sequence=int(row["sequence"]),
        kind=row["kind"],
        payload_json=json.loads(row["payload_json"]),
        emitted_at=datetime.fromisoformat(row["emitted_at"]),
    )


def _row_to_task(
    row: dict[str, Any], status_override: TaskStatus | None = None
) -> Task:
    return Task(
        task_id=row["task_id"],
        session_id=UUID(row["session_id"]),
        team_id=row["team_id"],
        kind=row["kind"],
        payload_json=json.loads(row["payload_json"]),
        status=status_override or TaskStatus(row["status"]),
        enqueued_at=datetime.fromisoformat(row["enqueued_at"]),
        started_at=(
            datetime.fromisoformat(row["started_at"]) if row["started_at"] else None
        ),
        completed_at=(
            datetime.fromisoformat(row["completed_at"])
            if row["completed_at"]
            else None
        ),
        result_json=(
            json.loads(row["result_json"]) if row["result_json"] else None
        ),
    )


def _row_to_request(
    row: dict[str, Any], status_override: RequestStatus | None
) -> Request:
    return Request(
        request_id=row["request_id"],
        session_id=UUID(row["session_id"]),
        from_team=row["from_team"],
        to_team=row["to_team"],
        kind=row["kind"],
        input_json=json.loads(row["input_json"]),
        status=status_override or RequestStatus(row["status"]),
        response_json=(
            json.loads(row["response_json"]) if row["response_json"] else None
        ),
        parent_request_id=row["parent_request_id"],
        enqueued_at=datetime.fromisoformat(row["enqueued_at"]),
        in_flight_at=(
            datetime.fromisoformat(row["in_flight_at"])
            if row["in_flight_at"]
            else None
        ),
        completed_at=(
            datetime.fromisoformat(row["completed_at"])
            if row["completed_at"]
            else None
        ),
        timeout_at=datetime.fromisoformat(row["timeout_at"]),
    )
