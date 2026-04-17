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
    Body,
    BodyFormat,
    Event,
    Finding,
    Gate,
    Message,
    NodeDependency,
    NodeKind,
    NodeStateEvent,
    NodeStateEventType,
    PlanNode,
    Request,
    RequestStatus,
    Result,
    Roadmap,
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
                creation_date=datetime.fromisoformat(existing["creation_date"]),
                completion_date=(
                    datetime.fromisoformat(existing["completion_date"])
                    if existing["completion_date"]
                    else None
                ),
                metadata_json=json.loads(existing["metadata_json"]),
            )
        now = _utcnow_iso()
        row = {
            "session_id": str(session_id),
            "initial_team_id": initial_team_id,
            "status": SessionStatus.OPEN.value,
            "creation_date": now,
            "completion_date": None,
            "metadata_json": json.dumps(metadata or {}),
        }
        await self._storage.insert("session", row)
        return Session(
            session_id=session_id,
            initial_team_id=initial_team_id,
            status=SessionStatus.OPEN,
            creation_date=datetime.fromisoformat(now),
            metadata_json=metadata or {},
        )

    async def close_session(
        self, session_id: UUID, status: SessionStatus
    ) -> None:
        await self._storage.update(
            "session",
            {"session_id": str(session_id)},
            {"status": status.value, "completion_date": _utcnow_iso()},
        )

    # ---- State tree -------------------------------------------------------

    async def push_state(
        self,
        session_id: UUID,
        team_id: str,
        state_name: str,
        parent_node_id: str | None,
        plan_node_id: str | None = None,
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
                "plan_node_id": plan_node_id,
                "state_name": state_name,
                "status": StateStatus.ACTIVE.value,
                "entry_date": now,
                "exit_date": None,
            },
        )
        return StateNode(
            node_id=node_id,
            session_id=session_id,
            team_id=team_id,
            parent_node_id=parent_node_id,
            state_name=state_name,
            status=StateStatus.ACTIVE,
            entry_date=datetime.fromisoformat(now),
            plan_node_id=plan_node_id,
        )

    async def pop_state(
        self, node_id: str, status: StateStatus = StateStatus.COMPLETED
    ) -> None:
        await self._storage.update(
            "state",
            {"node_id": node_id},
            {"status": status.value, "exit_date": _utcnow_iso()},
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
            order_by="entry_date",
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
        plan_node_id: str | None = None,
    ) -> Message:
        message_id = _new_id("msg")
        now = _utcnow_iso()
        await self._storage.insert(
            "message",
            {
                "message_id": message_id,
                "session_id": str(session_id),
                "team_id": team_id,
                "plan_node_id": plan_node_id,
                "direction": direction,
                "type": type,
                "creation_date": now,
            },
        )
        await self.set_body("message", message_id, body, BodyFormat.PLAIN)
        return Message(
            message_id=message_id,
            session_id=session_id,
            team_id=team_id,
            direction=direction,
            type=type,
            body=body,
            creation_date=datetime.fromisoformat(now),
            plan_node_id=plan_node_id,
        )

    async def list_messages(
        self, session_id: UUID, team_id: str | None = None
    ) -> list[Message]:
        where: dict[str, Any] = {"session_id": str(session_id)}
        if team_id is not None:
            where["team_id"] = team_id
        rows = await self._storage.fetch_all(
            "message", where=where, order_by="creation_date"
        )
        messages: list[Message] = []
        for r in rows:
            body = await self.get_body("message", r["message_id"])
            messages.append(_row_to_message(r, body.body_text if body else ""))
        return messages

    # ---- Gates ------------------------------------------------------------

    async def create_gate(
        self,
        session_id: UUID,
        team_id: str,
        category: str,
        options: list[str],
        plan_node_id: str | None = None,
    ) -> Gate:
        gate_id = _new_id("gate")
        now = _utcnow_iso()
        await self._storage.insert(
            "gate",
            {
                "gate_id": gate_id,
                "session_id": str(session_id),
                "team_id": team_id,
                "plan_node_id": plan_node_id,
                "category": category,
                "options_json": json.dumps(options),
                "verdict": None,
                "creation_date": now,
                "verdict_date": None,
            },
        )
        return Gate(
            gate_id=gate_id,
            session_id=session_id,
            team_id=team_id,
            category=category,
            options_json=options,
            verdict=None,
            creation_date=datetime.fromisoformat(now),
            plan_node_id=plan_node_id,
        )

    async def resolve_gate(self, gate_id: str, verdict: str) -> None:
        await self._storage.update(
            "gate",
            {"gate_id": gate_id},
            {"verdict": verdict, "verdict_date": _utcnow_iso()},
        )

    # ---- Results / Findings ----------------------------------------------

    async def create_result(
        self,
        session_id: UUID,
        team_id: str,
        specialist_id: str,
        passed: bool,
        summary: dict[str, Any],
        plan_node_id: str | None = None,
    ) -> Result:
        result_id = _new_id("res")
        now = _utcnow_iso()
        await self._storage.insert(
            "result",
            {
                "result_id": result_id,
                "session_id": str(session_id),
                "team_id": team_id,
                "plan_node_id": plan_node_id,
                "specialist_id": specialist_id,
                "passed": 1 if passed else 0,
                "summary_json": json.dumps(summary),
                "creation_date": now,
            },
        )
        return Result(
            result_id=result_id,
            session_id=session_id,
            team_id=team_id,
            specialist_id=specialist_id,
            passed=passed,
            summary_json=summary,
            creation_date=datetime.fromisoformat(now),
            plan_node_id=plan_node_id,
        )

    async def list_results(
        self, session_id: UUID, team_id: str | None = None
    ) -> list[Result]:
        where: dict[str, Any] = {"session_id": str(session_id)}
        if team_id is not None:
            where["team_id"] = team_id
        rows = await self._storage.fetch_all(
            "result", where=where, order_by="creation_date"
        )
        return [_row_to_result(r) for r in rows]

    async def create_finding(
        self,
        result_id: str,
        kind: str,
        severity: str,
        body: str,
        source_artifact: str | None = None,
        plan_node_id: str | None = None,
    ) -> Finding:
        finding_id = _new_id("find")
        now = _utcnow_iso()
        await self._storage.insert(
            "finding",
            {
                "finding_id": finding_id,
                "result_id": result_id,
                "plan_node_id": plan_node_id,
                "kind": kind,
                "severity": severity,
                "source_artifact": source_artifact,
                "creation_date": now,
            },
        )
        await self.set_body("finding", finding_id, body, BodyFormat.PLAIN)
        return Finding(
            finding_id=finding_id,
            result_id=result_id,
            kind=kind,
            severity=severity,
            body=body,
            source_artifact=source_artifact,
            creation_date=datetime.fromisoformat(now),
            plan_node_id=plan_node_id,
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
        plan_node_id: str | None = None,
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
                "plan_node_id": plan_node_id,
                "dispatch_id": dispatch_id,
                "sequence": seq,
                "kind": kind,
                "payload_json": json.dumps(payload),
                "event_date": now,
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
            event_date=datetime.fromisoformat(now),
            plan_node_id=plan_node_id,
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
        plan_node_id: str | None = None,
    ) -> Task:
        task_id = _new_id("task")
        now = _utcnow_iso()
        await self._storage.insert(
            "task",
            {
                "task_id": task_id,
                "session_id": str(session_id),
                "team_id": team_id,
                "plan_node_id": plan_node_id,
                "kind": kind,
                "payload_json": json.dumps(payload),
                "status": TaskStatus.PENDING.value,
                "scheduled_date": now,
                "start_date": None,
                "completion_date": None,
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
            scheduled_date=datetime.fromisoformat(now),
            plan_node_id=plan_node_id,
        )

    async def next_task(self, session_id: UUID) -> Task | None:
        rows = await self._storage.fetch_all(
            "task",
            where={
                "session_id": str(session_id),
                "status": TaskStatus.PENDING.value,
            },
            order_by="scheduled_date",
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
                "start_date": _utcnow_iso(),
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
                "completion_date": _utcnow_iso(),
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
        plan_node_id: str | None = None,
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
                "plan_node_id": plan_node_id,
                "kind": kind,
                "input_json": json.dumps(input_data),
                "status": RequestStatus.PENDING.value,
                "response_json": None,
                "parent_request_id": parent_request_id,
                "creation_date": now.isoformat(),
                "start_date": None,
                "completion_date": None,
                "timeout_date": (now + timedelta(seconds=timeout)).isoformat(),
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
            creation_date=now,
            start_date=None,
            completion_date=None,
            timeout_date=now + timedelta(seconds=timeout),
            plan_node_id=plan_node_id,
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
            order_by="creation_date",
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
                "start_date": _utcnow_iso(),
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
                "completion_date": _utcnow_iso(),
            },
        )

    async def get_request(self, request_id: str) -> Request | None:
        row = await self._storage.fetch_one(
            "request", {"request_id": request_id}
        )
        return _row_to_request(row, None) if row else None

    # ---- Project-management resources (spec §6.1) ------------------------

    async def create_schedule_item(
        self,
        session_id: UUID,
        team_id: str,
        milestone_name: str,
        status: str,
        target_date: str | None = None,
    ) -> dict[str, Any]:
        schedule_id = _new_id("sched")
        row = {
            "schedule_id": schedule_id,
            "session_id": str(session_id),
            "team_id": team_id,
            "milestone_name": milestone_name,
            "target_date": target_date,
            "status": status,
            "creation_date": _utcnow_iso(),
        }
        await self._storage.insert("schedule", row)
        return row

    async def list_schedule_items(
        self, session_id: UUID, team_id: str | None = None
    ) -> list[dict[str, Any]]:
        where: dict[str, Any] = {"session_id": str(session_id)}
        if team_id is not None:
            where["team_id"] = team_id
        return await self._storage.fetch_all(
            "schedule", where=where, order_by="creation_date"
        )

    async def create_todo_item(
        self,
        session_id: UUID,
        team_id: str,
        title: str,
        status: str,
        owner: str | None = None,
        milestone_name: str | None = None,
    ) -> dict[str, Any]:
        todo_id = _new_id("todo")
        row = {
            "todo_id": todo_id,
            "session_id": str(session_id),
            "team_id": team_id,
            "title": title,
            "status": status,
            "owner": owner,
            "milestone_name": milestone_name,
            "creation_date": _utcnow_iso(),
        }
        await self._storage.insert("todo", row)
        return row

    async def list_todo_items(
        self, session_id: UUID, team_id: str | None = None
    ) -> list[dict[str, Any]]:
        where: dict[str, Any] = {"session_id": str(session_id)}
        if team_id is not None:
            where["team_id"] = team_id
        return await self._storage.fetch_all(
            "todo", where=where, order_by="creation_date"
        )

    async def create_decision_item(
        self,
        session_id: UUID,
        team_id: str,
        title: str,
        rationale: str,
        decided_by: str | None = None,
        plan_node_id: str | None = None,
    ) -> dict[str, Any]:
        decision_id = _new_id("dec")
        row = {
            "decision_id": decision_id,
            "session_id": str(session_id),
            "team_id": team_id,
            "plan_node_id": plan_node_id,
            "title": title,
            "decided_by": decided_by,
            "creation_date": _utcnow_iso(),
        }
        await self._storage.insert("decision", row)
        await self.set_body("decision", decision_id, rationale, BodyFormat.PLAIN)
        # Return a dict shaped like the old API (callers iterate over it).
        return {**row, "rationale": rationale}

    async def list_decision_items(
        self, session_id: UUID, team_id: str | None = None
    ) -> list[dict[str, Any]]:
        where: dict[str, Any] = {"session_id": str(session_id)}
        if team_id is not None:
            where["team_id"] = team_id
        rows = await self._storage.fetch_all(
            "decision", where=where, order_by="creation_date"
        )
        # Attach rationale from body side-table.
        out: list[dict[str, Any]] = []
        for r in rows:
            body = await self.get_body("decision", r["decision_id"])
            out.append({**r, "rationale": body.body_text if body else ""})
        return out

    # ---- Roadmap ----------------------------------------------------------
    #
    # Project-scoped resources (persist across sessions). See
    # docs/planning/2026-04-17-atp-roadmap-design.md.

    async def create_roadmap(self, title: str, roadmap_id: str | None = None) -> Roadmap:
        rid = roadmap_id or _new_id("rm")
        now = _utcnow_iso()
        await self._storage.insert(
            "roadmap",
            {
                "roadmap_id": rid,
                "title": title,
                "creation_date": now,
                "modification_date": now,
            },
        )
        return Roadmap(
            roadmap_id=rid,
            title=title,
            creation_date=datetime.fromisoformat(now),
            modification_date=datetime.fromisoformat(now),
        )

    async def get_roadmap(self, roadmap_id: str) -> Roadmap | None:
        row = await self._storage.fetch_one("roadmap", {"roadmap_id": roadmap_id})
        if not row:
            return None
        return _row_to_roadmap(row)

    async def create_plan_node(
        self,
        roadmap_id: str,
        title: str,
        node_kind: NodeKind,
        *,
        parent_id: str | None = None,
        position: float = 1.0,
        specialist: str | None = None,
        speciality: str | None = None,
        node_id: str | None = None,
    ) -> PlanNode:
        nid = node_id or _new_id("node")
        now = _utcnow_iso()
        await self._storage.insert(
            "plan_node",
            {
                "node_id": nid,
                "roadmap_id": roadmap_id,
                "parent_id": parent_id,
                "position": position,
                "node_kind": node_kind.value,
                "title": title,
                "specialist": specialist,
                "speciality": speciality,
                "creation_date": now,
                "modification_date": now,
            },
        )
        return PlanNode(
            node_id=nid,
            roadmap_id=roadmap_id,
            parent_id=parent_id,
            position=position,
            node_kind=node_kind,
            title=title,
            specialist=specialist,
            speciality=speciality,
            creation_date=datetime.fromisoformat(now),
            modification_date=datetime.fromisoformat(now),
        )

    async def get_plan_node(self, node_id: str) -> PlanNode | None:
        row = await self._storage.fetch_one("plan_node", {"node_id": node_id})
        if not row:
            return None
        return _row_to_plan_node(row)

    async def list_plan_nodes(self, roadmap_id: str) -> list[PlanNode]:
        """List every plan_node in the roadmap, ordered by position.

        To filter by parent, use `list_plan_nodes_by_parent`.
        """
        rows = await self._storage.fetch_all(
            "plan_node", where={"roadmap_id": roadmap_id}, order_by="position",
        )
        return [_row_to_plan_node(r) for r in rows]

    async def list_plan_nodes_by_parent(
        self, roadmap_id: str, parent_id: str | None
    ) -> list[PlanNode]:
        """List direct children of a parent (or roots when parent_id=None).

        Needed because fetch_all treats None as 'filter absent' rather than
        'IS NULL'. Roots are queried through a small inline query here.
        """
        storage = self._storage
        if parent_id is None:
            rows = await storage.fetch_all(
                "plan_node",
                where={"roadmap_id": roadmap_id},
                order_by="position",
            )
            return [_row_to_plan_node(r) for r in rows if r["parent_id"] is None]
        rows = await storage.fetch_all(
            "plan_node",
            where={"roadmap_id": roadmap_id, "parent_id": parent_id},
            order_by="position",
        )
        return [_row_to_plan_node(r) for r in rows]

    async def add_dependency(
        self, node_id: str, depends_on_id: str
    ) -> NodeDependency:
        """Add a DAG edge. Raises CycleError if it would create a cycle."""
        if await self._would_create_cycle(node_id, depends_on_id):
            raise CycleError(
                f"adding ({node_id} depends_on {depends_on_id}) would create a cycle"
            )
        now = _utcnow_iso()
        await self._storage.insert(
            "node_dependency",
            {
                "node_id": node_id,
                "depends_on_id": depends_on_id,
                "creation_date": now,
            },
        )
        # Read back to pick up the AUTOINCREMENT dependency_id.
        rows = await self._storage.fetch_all(
            "node_dependency",
            where={"node_id": node_id, "depends_on_id": depends_on_id},
        )
        r = rows[-1]
        return NodeDependency(
            dependency_id=r["dependency_id"],
            node_id=r["node_id"],
            depends_on_id=r["depends_on_id"],
            creation_date=datetime.fromisoformat(r["creation_date"]),
        )

    async def list_dependencies_of(self, node_id: str) -> list[NodeDependency]:
        rows = await self._storage.fetch_all(
            "node_dependency", where={"node_id": node_id}
        )
        return [
            NodeDependency(
                dependency_id=r["dependency_id"],
                node_id=r["node_id"],
                depends_on_id=r["depends_on_id"],
                creation_date=datetime.fromisoformat(r["creation_date"]),
            )
            for r in rows
        ]

    async def record_node_state_event(
        self,
        node_id: str,
        event_type: NodeStateEventType,
        actor: str,
        session_id: UUID | None = None,
    ) -> NodeStateEvent:
        now = _utcnow_iso()
        await self._storage.insert(
            "node_state_event",
            {
                "node_id": node_id,
                "session_id": str(session_id) if session_id else None,
                "event_type": event_type.value,
                "actor": actor,
                "event_date": now,
            },
        )
        rows = await self._storage.fetch_all(
            "node_state_event",
            where={"node_id": node_id},
            order_by="event_id DESC",
            limit=1,
        )
        r = rows[0]
        return NodeStateEvent(
            event_id=r["event_id"],
            node_id=r["node_id"],
            session_id=UUID(r["session_id"]) if r["session_id"] else None,
            event_type=NodeStateEventType(r["event_type"]),
            actor=r["actor"],
            event_date=datetime.fromisoformat(r["event_date"]),
        )

    async def latest_node_state(self, node_id: str) -> NodeStateEvent | None:
        rows = await self._storage.fetch_all(
            "node_state_event",
            where={"node_id": node_id},
            order_by="event_id DESC",
            limit=1,
        )
        if not rows:
            return None
        r = rows[0]
        return NodeStateEvent(
            event_id=r["event_id"],
            node_id=r["node_id"],
            session_id=UUID(r["session_id"]) if r["session_id"] else None,
            event_type=NodeStateEventType(r["event_type"]),
            actor=r["actor"],
            event_date=datetime.fromisoformat(r["event_date"]),
        )

    # ---- Body side-table --------------------------------------------------

    async def set_body(
        self,
        owner_type: str,
        owner_id: str,
        body_text: str,
        body_format: BodyFormat = BodyFormat.MARKDOWN,
    ) -> Body:
        existing = await self._storage.fetch_one(
            "body", {"owner_type": owner_type, "owner_id": owner_id}
        )
        now = _utcnow_iso()
        if existing:
            await self._storage.update(
                "body",
                {"owner_type": owner_type, "owner_id": owner_id},
                {
                    "body_text": body_text,
                    "body_format": body_format.value,
                    "modification_date": now,
                },
            )
        else:
            await self._storage.insert(
                "body",
                {
                    "owner_type": owner_type,
                    "owner_id": owner_id,
                    "body_format": body_format.value,
                    "body_text": body_text,
                    "modification_date": now,
                },
            )
        return Body(
            owner_type=owner_type,
            owner_id=owner_id,
            body_format=body_format,
            body_text=body_text,
            modification_date=datetime.fromisoformat(now),
        )

    async def get_body(self, owner_type: str, owner_id: str) -> Body | None:
        row = await self._storage.fetch_one(
            "body", {"owner_type": owner_type, "owner_id": owner_id}
        )
        if not row:
            return None
        return Body(
            owner_type=row["owner_type"],
            owner_id=row["owner_id"],
            body_format=BodyFormat(row["body_format"]),
            body_text=row["body_text"],
            modification_date=datetime.fromisoformat(row["modification_date"]),
        )

    # ---- Internal helpers -------------------------------------------------

    async def _would_create_cycle(
        self, dependent: str, prerequisite: str
    ) -> bool:
        """True if adding (dependent depends_on prerequisite) creates a cycle."""
        if dependent == prerequisite:
            return True
        visited: set[str] = {prerequisite}
        frontier = [prerequisite]
        while frontier:
            current = frontier.pop()
            rows = await self._storage.fetch_all(
                "node_dependency", where={"node_id": current}
            )
            for r in rows:
                nxt = r["depends_on_id"]
                if nxt == dependent:
                    return True
                if nxt not in visited:
                    visited.add(nxt)
                    frontier.append(nxt)
        return False


class CycleError(ValueError):
    """Raised when adding a node_dependency edge would create a cycle."""


# ---------------------------------------------------------------------------
# Row → dataclass helpers
# ---------------------------------------------------------------------------


def _row_to_roadmap(row: dict[str, Any]) -> Roadmap:
    return Roadmap(
        roadmap_id=row["roadmap_id"],
        title=row["title"],
        creation_date=datetime.fromisoformat(row["creation_date"]),
        modification_date=datetime.fromisoformat(row["modification_date"]),
    )


def _row_to_plan_node(row: dict[str, Any]) -> PlanNode:
    return PlanNode(
        node_id=row["node_id"],
        roadmap_id=row["roadmap_id"],
        parent_id=row["parent_id"],
        position=row["position"],
        node_kind=NodeKind(row["node_kind"]),
        title=row["title"],
        specialist=row["specialist"],
        speciality=row["speciality"],
        creation_date=datetime.fromisoformat(row["creation_date"]),
        modification_date=datetime.fromisoformat(row["modification_date"]),
    )


def _row_to_state_node(row: dict[str, Any]) -> StateNode:
    return StateNode(
        node_id=row["node_id"],
        session_id=UUID(row["session_id"]),
        team_id=row["team_id"],
        parent_node_id=row["parent_node_id"],
        state_name=row["state_name"],
        status=StateStatus(row["status"]),
        entry_date=datetime.fromisoformat(row["entry_date"]),
        exit_date=(
            datetime.fromisoformat(row["exit_date"]) if row["exit_date"] else None
        ),
        plan_node_id=row.get("plan_node_id"),
    )


def _row_to_message(row: dict[str, Any], body: str) -> Message:
    return Message(
        message_id=row["message_id"],
        session_id=UUID(row["session_id"]),
        team_id=row["team_id"],
        direction=row["direction"],
        type=row["type"],
        body=body,
        creation_date=datetime.fromisoformat(row["creation_date"]),
        plan_node_id=row.get("plan_node_id"),
    )


def _row_to_result(row: dict[str, Any]) -> Result:
    return Result(
        result_id=row["result_id"],
        session_id=UUID(row["session_id"]),
        team_id=row["team_id"],
        specialist_id=row["specialist_id"],
        passed=bool(row["passed"]),
        summary_json=json.loads(row["summary_json"]),
        creation_date=datetime.fromisoformat(row["creation_date"]),
        plan_node_id=row.get("plan_node_id"),
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
        event_date=datetime.fromisoformat(row["event_date"]),
        plan_node_id=row.get("plan_node_id"),
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
        scheduled_date=datetime.fromisoformat(row["scheduled_date"]),
        start_date=(
            datetime.fromisoformat(row["start_date"]) if row["start_date"] else None
        ),
        completion_date=(
            datetime.fromisoformat(row["completion_date"])
            if row["completion_date"]
            else None
        ),
        result_json=(
            json.loads(row["result_json"]) if row["result_json"] else None
        ),
        plan_node_id=row.get("plan_node_id"),
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
        creation_date=datetime.fromisoformat(row["creation_date"]),
        start_date=(
            datetime.fromisoformat(row["start_date"])
            if row["start_date"]
            else None
        ),
        completion_date=(
            datetime.fromisoformat(row["completion_date"])
            if row["completion_date"]
            else None
        ),
        timeout_date=datetime.fromisoformat(row["timeout_date"]),
        plan_node_id=row.get("plan_node_id"),
    )
