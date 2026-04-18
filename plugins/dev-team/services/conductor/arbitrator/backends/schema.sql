-- Conductor arbitrator — SQLite schema
-- Resource tables from spec §6.1. Indexes from §6.3.
-- Keys: (session_id, team_id) on everything except `request` which has from/to.

CREATE TABLE IF NOT EXISTS session (
    session_id          TEXT PRIMARY KEY,
    initial_team_id     TEXT NOT NULL,
    status              TEXT NOT NULL,
    roadmap_id          TEXT,                        -- optional: roadmap this session drives
    last_decision_date  TEXT,                        -- for "no new findings since" short-circuit
    creation_date       TEXT NOT NULL,
    completion_date     TEXT,
    metadata_json       TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS state (
    node_id           TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    team_id           TEXT NOT NULL,
    parent_node_id    TEXT,
    plan_node_id      TEXT,                         -- optional: roadmap node this dispatch addresses
    state_name        TEXT NOT NULL,
    status            TEXT NOT NULL,
    entry_date        TEXT NOT NULL,
    exit_date         TEXT,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);
CREATE INDEX IF NOT EXISTS idx_state_session_parent
    ON state(session_id, parent_node_id);
CREATE INDEX IF NOT EXISTS idx_state_plan_node
    ON state(plan_node_id);

CREATE TABLE IF NOT EXISTS message (
    message_id        TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    team_id           TEXT NOT NULL,
    plan_node_id      TEXT,                         -- optional: roadmap node this message is about
    direction         TEXT NOT NULL,
    type              TEXT NOT NULL,
    -- narrative body lives in body(owner_type='message', owner_id=message_id)
    creation_date     TEXT NOT NULL,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);
CREATE INDEX IF NOT EXISTS idx_message_session_created
    ON message(session_id, creation_date);
CREATE INDEX IF NOT EXISTS idx_message_plan_node
    ON message(plan_node_id);

CREATE TABLE IF NOT EXISTS gate (
    gate_id           TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    team_id           TEXT NOT NULL,
    plan_node_id      TEXT,                         -- optional: roadmap node this gate is about
    category          TEXT NOT NULL,
    options_json      TEXT NOT NULL,
    verdict           TEXT,
    creation_date     TEXT NOT NULL,
    verdict_date      TEXT,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);
CREATE INDEX IF NOT EXISTS idx_gate_plan_node ON gate(plan_node_id);

CREATE TABLE IF NOT EXISTS result (
    result_id         TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    team_id           TEXT NOT NULL,
    plan_node_id      TEXT,                         -- optional: roadmap node this result is about
    specialist_id     TEXT NOT NULL,
    passed            INTEGER NOT NULL,
    summary_json      TEXT NOT NULL,
    creation_date     TEXT NOT NULL,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);
CREATE INDEX IF NOT EXISTS idx_result_plan_node ON result(plan_node_id);

CREATE TABLE IF NOT EXISTS finding (
    finding_id        TEXT PRIMARY KEY,
    result_id         TEXT NOT NULL,
    plan_node_id      TEXT,                         -- optional: roadmap node this finding concerns
    kind              TEXT NOT NULL,
    severity          TEXT NOT NULL,
    -- narrative body lives in body(owner_type='finding', owner_id=finding_id)
    source_artifact   TEXT,
    creation_date     TEXT NOT NULL,
    FOREIGN KEY (result_id)    REFERENCES result(result_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);
CREATE INDEX IF NOT EXISTS idx_finding_result    ON finding(result_id);
CREATE INDEX IF NOT EXISTS idx_finding_plan_node ON finding(plan_node_id);

CREATE TABLE IF NOT EXISTS event (
    event_id          TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    team_id           TEXT,
    agent_id          TEXT,
    plan_node_id      TEXT,                         -- optional: roadmap node this event concerns
    dispatch_id       TEXT,
    sequence          INTEGER NOT NULL,
    kind              TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    event_date        TEXT NOT NULL,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);
CREATE INDEX IF NOT EXISTS idx_event_session_sequence
    ON event(session_id, sequence);
CREATE INDEX IF NOT EXISTS idx_event_plan_node
    ON event(plan_node_id);

CREATE TABLE IF NOT EXISTS task (
    task_id           TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    team_id           TEXT NOT NULL,
    plan_node_id      TEXT,                         -- optional: roadmap node this task serves
    kind              TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    status            TEXT NOT NULL,
    scheduled_date    TEXT NOT NULL,
    start_date        TEXT,
    completion_date   TEXT,
    result_json       TEXT,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);
CREATE INDEX IF NOT EXISTS idx_task_session_status_scheduled
    ON task(session_id, status, scheduled_date);
CREATE INDEX IF NOT EXISTS idx_task_plan_node
    ON task(plan_node_id);

CREATE TABLE IF NOT EXISTS request (
    request_id        TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    from_team         TEXT NOT NULL,
    to_team           TEXT NOT NULL,
    plan_node_id      TEXT,                         -- optional: roadmap node this request advances
    kind              TEXT NOT NULL,
    input_json        TEXT NOT NULL,
    status            TEXT NOT NULL,
    response_json     TEXT,
    parent_request_id TEXT,
    creation_date     TEXT NOT NULL,
    start_date        TEXT,
    completion_date   TEXT,
    timeout_date      TEXT NOT NULL,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);
CREATE INDEX IF NOT EXISTS idx_request_session_status_created
    ON request(session_id, status, creation_date);
CREATE INDEX IF NOT EXISTS idx_request_plan_node
    ON request(plan_node_id);

-- ---------------------------------------------------------------------------
-- Project-management resources (absorbed from project-storage-provider,
-- spec §6.1). Minimal columns for step 4: only the fields a future query
-- would WHERE/ORDER BY. No blob columns.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS schedule (
    schedule_id    TEXT PRIMARY KEY,
    session_id     TEXT NOT NULL,
    team_id        TEXT NOT NULL,
    milestone_name TEXT NOT NULL,
    target_date    TEXT,
    status         TEXT NOT NULL,
    creation_date  TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES session(session_id)
);
CREATE INDEX IF NOT EXISTS idx_schedule_session_team
    ON schedule(session_id, team_id);

CREATE TABLE IF NOT EXISTS todo (
    todo_id        TEXT PRIMARY KEY,
    session_id     TEXT NOT NULL,
    team_id        TEXT NOT NULL,
    title          TEXT NOT NULL,
    status         TEXT NOT NULL,
    owner          TEXT,
    milestone_name TEXT,
    creation_date  TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES session(session_id)
);
CREATE INDEX IF NOT EXISTS idx_todo_session_team
    ON todo(session_id, team_id);
CREATE INDEX IF NOT EXISTS idx_todo_session_status
    ON todo(session_id, status);

CREATE TABLE IF NOT EXISTS decision (
    decision_id    TEXT PRIMARY KEY,
    session_id     TEXT NOT NULL,
    team_id        TEXT NOT NULL,
    plan_node_id   TEXT,                          -- optional: roadmap node this decision concerns
    title          TEXT NOT NULL,
    -- rationale lives in body(owner_type='decision', owner_id=decision_id)
    decided_by     TEXT,
    creation_date  TEXT NOT NULL,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);
CREATE INDEX IF NOT EXISTS idx_decision_session_team
    ON decision(session_id, team_id);

-- ---------------------------------------------------------------------------
-- Roadmap graph (project-scoped; persists across sessions).
-- See docs/planning/2026-04-17-atp-roadmap-design.md for design rationale.
-- The graph has two projections: tree via parent_id, DAG via node_dependency.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS roadmap (
    roadmap_id        TEXT PRIMARY KEY,
    title             TEXT NOT NULL,
    creation_date     TEXT NOT NULL,
    modification_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plan_node (
    node_id           TEXT PRIMARY KEY,
    roadmap_id        TEXT NOT NULL,
    parent_id         TEXT,                         -- NULL = root
    position          REAL NOT NULL,                -- fractional index for order
    node_kind         TEXT NOT NULL,                -- compound | primitive
    title             TEXT NOT NULL,
    specialist        TEXT,
    speciality        TEXT,
    creation_date     TEXT NOT NULL,
    modification_date TEXT NOT NULL,
    FOREIGN KEY (roadmap_id) REFERENCES roadmap(roadmap_id),
    FOREIGN KEY (parent_id)  REFERENCES plan_node(node_id)
);
CREATE INDEX IF NOT EXISTS idx_plan_node_tree
    ON plan_node(roadmap_id, parent_id, position);

CREATE TABLE IF NOT EXISTS node_dependency (
    dependency_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id           TEXT NOT NULL,                -- dependent
    depends_on_id     TEXT NOT NULL,                -- prerequisite
    creation_date     TEXT NOT NULL,
    UNIQUE (node_id, depends_on_id),
    FOREIGN KEY (node_id)       REFERENCES plan_node(node_id),
    FOREIGN KEY (depends_on_id) REFERENCES plan_node(node_id)
);
CREATE INDEX IF NOT EXISTS idx_node_dep_from ON node_dependency(node_id);
CREATE INDEX IF NOT EXISTS idx_node_dep_to   ON node_dependency(depends_on_id);

CREATE TABLE IF NOT EXISTS node_state_event (
    event_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id           TEXT NOT NULL,
    session_id        TEXT,                         -- which session drove this
    event_type        TEXT NOT NULL,                -- planned|ready|running|done|failed|superseded
    actor             TEXT NOT NULL,
    event_date        TEXT NOT NULL,
    FOREIGN KEY (node_id) REFERENCES plan_node(node_id)
);
CREATE INDEX IF NOT EXISTS idx_nse_latest
    ON node_state_event(node_id, event_date DESC);

-- ---------------------------------------------------------------------------
-- Body side-table: one place for narrative content.
-- Primary rows stay lean; narrative routes through (owner_type, owner_id).
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS body (
    owner_type        TEXT NOT NULL,
    owner_id          TEXT NOT NULL,
    body_format       TEXT NOT NULL,                -- markdown|plain|json
    body_text         TEXT NOT NULL,
    modification_date TEXT NOT NULL,
    PRIMARY KEY (owner_type, owner_id)
);
