-- atp database schema v3
-- Reference schema for the roadmap system described in
--   docs/planning/2026-04-17-atp-roadmap-design.md
--
-- Conforms to .claude/rules/db-schema-design.md:
--   - No blob columns in primary rows (narrative content is isolated in `body`)
--   - No computed values (counts/percentages derive from queries)
--   - No unstructured lists (dependencies, options, properties get own tables)
--   - creation_date / modification_date naming
--   - Project vocabulary (specialist, speciality, team-lead)
--   - Flexible *_kind type columns instead of predicted enums
--   - Separate tables when 1-to-many or written-later
--
-- The live conductor schema at
--   services/conductor/arbitrator/backends/schema.sql
-- will converge on this design in a follow-up plan.

-- ===========================================================================
-- Roadmap (project-scoped; survives across conductor sessions)
-- ===========================================================================

CREATE TABLE roadmap (
    roadmap_id          TEXT PRIMARY KEY,
    title               TEXT NOT NULL,
    creation_date       DATETIME NOT NULL,
    modification_date   DATETIME NOT NULL
);

CREATE TABLE plan_node (
    node_id             TEXT PRIMARY KEY,
    roadmap_id          TEXT NOT NULL,
    parent_id           TEXT,
    position            REAL NOT NULL,
    node_kind           TEXT NOT NULL,
    title               TEXT NOT NULL,
    specialist          TEXT,
    speciality          TEXT,
    creation_date       DATETIME NOT NULL,
    modification_date   DATETIME NOT NULL,
    FOREIGN KEY (roadmap_id) REFERENCES roadmap(roadmap_id),
    FOREIGN KEY (parent_id)  REFERENCES plan_node(node_id)
);

CREATE TABLE node_dependency (
    dependency_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id             TEXT NOT NULL,
    depends_on_id       TEXT NOT NULL,
    creation_date       DATETIME NOT NULL,
    UNIQUE (node_id, depends_on_id),
    FOREIGN KEY (node_id)       REFERENCES plan_node(node_id),
    FOREIGN KEY (depends_on_id) REFERENCES plan_node(node_id)
);

CREATE TABLE node_state_event (
    event_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id             TEXT NOT NULL,
    session_id          TEXT,
    event_type          TEXT NOT NULL,
    actor               TEXT NOT NULL,
    event_date          DATETIME NOT NULL,
    FOREIGN KEY (node_id) REFERENCES plan_node(node_id)
);

-- ===========================================================================
-- Session & runtime (per-session)
-- ===========================================================================

CREATE TABLE session (
    session_id              TEXT PRIMARY KEY,
    playbook                TEXT NOT NULL,
    roadmap_id              TEXT,
    plan_node_id            TEXT,
    host                    TEXT NOT NULL,
    pid                     INTEGER,
    status                  TEXT NOT NULL,
    ui_mode                 TEXT NOT NULL,
    last_task_id            TEXT,
    last_state_id           TEXT,
    last_event_sequence     INTEGER,
    creation_date           DATETIME NOT NULL,
    modification_date       DATETIME NOT NULL,
    completion_date         DATETIME,
    FOREIGN KEY (roadmap_id)   REFERENCES roadmap(roadmap_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE session_property (
    session_id          TEXT NOT NULL,
    property_key        TEXT NOT NULL,
    property_value      TEXT NOT NULL,
    modification_date   DATETIME NOT NULL,
    PRIMARY KEY (session_id, property_key),
    FOREIGN KEY (session_id) REFERENCES session(session_id)
);

CREATE TABLE team (
    session_id          TEXT NOT NULL,
    team_id             TEXT NOT NULL,
    team_playbook       TEXT NOT NULL,
    team_role           TEXT NOT NULL,
    status              TEXT NOT NULL,
    creation_date       DATETIME NOT NULL,
    modification_date   DATETIME NOT NULL,
    PRIMARY KEY (session_id, team_id),
    FOREIGN KEY (session_id) REFERENCES session(session_id)
);

CREATE TABLE state (
    state_id            TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    team_id             TEXT NOT NULL,
    parent_state_id     TEXT,
    plan_node_id        TEXT,
    state_name          TEXT NOT NULL,
    actor               TEXT NOT NULL,
    status              TEXT NOT NULL,
    entry_date          DATETIME NOT NULL,
    exit_date           DATETIME,
    FOREIGN KEY (session_id)      REFERENCES session(session_id),
    FOREIGN KEY (parent_state_id) REFERENCES state(state_id),
    FOREIGN KEY (plan_node_id)    REFERENCES plan_node(node_id)
);

CREATE TABLE task (
    task_id             TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    team_id             TEXT NOT NULL,
    state_id            TEXT,
    task_kind           TEXT NOT NULL,
    status              TEXT NOT NULL,
    scheduled_date      DATETIME,
    started_date        DATETIME,
    completion_date     DATETIME,
    FOREIGN KEY (session_id) REFERENCES session(session_id),
    FOREIGN KEY (state_id)   REFERENCES state(state_id)
);

-- ===========================================================================
-- Transcript
-- ===========================================================================

CREATE TABLE message (
    message_id          TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    team_id             TEXT NOT NULL,
    plan_node_id        TEXT,
    from_actor          TEXT NOT NULL,
    to_actor            TEXT NOT NULL,
    message_type        TEXT NOT NULL,
    persona             TEXT,
    creation_date       DATETIME NOT NULL,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE gate (
    gate_id             TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    team_id             TEXT NOT NULL,
    plan_node_id        TEXT,
    gate_category       TEXT NOT NULL,
    status              TEXT NOT NULL,
    creation_date       DATETIME NOT NULL,
    verdict_date        DATETIME,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE gate_option (
    option_id           TEXT PRIMARY KEY,
    gate_id             TEXT NOT NULL,
    option_label        TEXT NOT NULL,
    position            INTEGER NOT NULL,
    FOREIGN KEY (gate_id) REFERENCES gate(gate_id)
);

CREATE TABLE verdict (
    verdict_id          TEXT PRIMARY KEY,
    gate_id             TEXT NOT NULL,
    option_id           TEXT NOT NULL,
    creation_date       DATETIME NOT NULL,
    FOREIGN KEY (gate_id)   REFERENCES gate(gate_id),
    FOREIGN KEY (option_id) REFERENCES gate_option(option_id)
);

-- ===========================================================================
-- Inter-team requests
-- ===========================================================================

CREATE TABLE request (
    request_id              TEXT PRIMARY KEY,
    session_id              TEXT NOT NULL,
    from_team               TEXT NOT NULL,
    to_team                 TEXT NOT NULL,
    parent_request_id       TEXT,
    plan_node_id            TEXT,
    request_kind            TEXT NOT NULL,
    status                  TEXT NOT NULL,
    timeout_date            DATETIME NOT NULL,
    creation_date           DATETIME NOT NULL,
    completion_date         DATETIME,
    FOREIGN KEY (session_id)        REFERENCES session(session_id),
    FOREIGN KEY (parent_request_id) REFERENCES request(request_id),
    FOREIGN KEY (plan_node_id)      REFERENCES plan_node(node_id)
);

-- ===========================================================================
-- Observer + dispatch + retry protocol
-- ===========================================================================

CREATE TABLE dispatch (
    dispatch_id         TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    team_id             TEXT NOT NULL,
    state_id            TEXT,
    plan_node_id        TEXT,
    agent_kind          TEXT NOT NULL,
    agent_name          TEXT NOT NULL,
    logical_model       TEXT NOT NULL,
    concrete_model      TEXT,
    status              TEXT NOT NULL,
    schema_valid        INTEGER NOT NULL DEFAULT 0,
    start_date          DATETIME NOT NULL,
    end_date            DATETIME,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (state_id)     REFERENCES state(state_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE result (
    result_id           TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    team_id             TEXT NOT NULL,
    specialist          TEXT NOT NULL,
    speciality          TEXT,
    plan_node_id        TEXT,
    state_id            TEXT,
    status              TEXT NOT NULL,
    creation_date       DATETIME NOT NULL,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id),
    FOREIGN KEY (state_id)     REFERENCES state(state_id)
);

CREATE TABLE attempt (
    attempt_id              TEXT PRIMARY KEY,
    result_id               TEXT NOT NULL,
    session_id              TEXT NOT NULL,
    attempt_kind            TEXT NOT NULL,
    owner_name              TEXT NOT NULL,
    attempt_number          INTEGER NOT NULL,
    worker_dispatch_id      TEXT NOT NULL,
    verifier_dispatch_id    TEXT,
    verdict                 TEXT,
    failure_reason          TEXT,
    start_date              DATETIME NOT NULL,
    end_date                DATETIME,
    UNIQUE (result_id, attempt_kind, attempt_number),
    FOREIGN KEY (result_id)            REFERENCES result(result_id),
    FOREIGN KEY (session_id)           REFERENCES session(session_id),
    FOREIGN KEY (worker_dispatch_id)   REFERENCES dispatch(dispatch_id),
    FOREIGN KEY (verifier_dispatch_id) REFERENCES dispatch(dispatch_id)
);

CREATE TABLE event (
    event_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT NOT NULL,
    team_id             TEXT,
    agent_id            TEXT,
    plan_node_id        TEXT,
    dispatch_id         TEXT,
    sequence            INTEGER NOT NULL,
    event_kind          TEXT NOT NULL,
    event_subtype       TEXT,
    event_date          DATETIME NOT NULL,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (dispatch_id)  REFERENCES dispatch(dispatch_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

-- ===========================================================================
-- Results detail (findings), artifacts, interpretations
-- ===========================================================================

CREATE TABLE finding (
    finding_id          TEXT PRIMARY KEY,
    result_id           TEXT NOT NULL,
    plan_node_id        TEXT,
    finding_kind        TEXT NOT NULL,
    severity            TEXT NOT NULL,
    creation_date       DATETIME NOT NULL,
    FOREIGN KEY (result_id)    REFERENCES result(result_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE interpretation (
    interpretation_id   TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    team_id             TEXT NOT NULL,
    finding_id          TEXT NOT NULL,
    plan_node_id        TEXT,
    persona             TEXT NOT NULL,
    creation_date       DATETIME NOT NULL,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (finding_id)   REFERENCES finding(finding_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE artifact (
    artifact_id         TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    team_id             TEXT NOT NULL,
    plan_node_id        TEXT,
    result_id           TEXT,
    artifact_kind       TEXT NOT NULL,
    artifact_path       TEXT NOT NULL,
    creation_date       DATETIME NOT NULL,
    FOREIGN KEY (session_id)   REFERENCES session(session_id),
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id),
    FOREIGN KEY (result_id)    REFERENCES result(result_id)
);

-- ===========================================================================
-- Cross-cutting annotations (not nodes in the graph)
-- ===========================================================================

CREATE TABLE concern (
    concern_id          TEXT PRIMARY KEY,
    session_id          TEXT,
    plan_node_id        TEXT,
    raised_by           TEXT NOT NULL,
    title               TEXT NOT NULL,
    severity            TEXT NOT NULL,
    status              TEXT NOT NULL,
    creation_date       DATETIME NOT NULL,
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

CREATE TABLE decision (
    decision_id         TEXT PRIMARY KEY,
    session_id          TEXT,
    plan_node_id        TEXT,
    title               TEXT NOT NULL,
    decided_by          TEXT NOT NULL,
    creation_date       DATETIME NOT NULL,
    FOREIGN KEY (plan_node_id) REFERENCES plan_node(node_id)
);

-- ===========================================================================
-- Body side-table: one place for all narrative content
-- ===========================================================================

CREATE TABLE body (
    owner_type          TEXT NOT NULL,
    owner_id            TEXT NOT NULL,
    body_format         TEXT NOT NULL,
    body_text           TEXT NOT NULL,
    modification_date   DATETIME NOT NULL,
    PRIMARY KEY (owner_type, owner_id)
);

-- ===========================================================================
-- Indexes
-- ===========================================================================

-- Roadmap traversal
CREATE INDEX idx_plan_node_tree  ON plan_node(roadmap_id, parent_id, position);
CREATE INDEX idx_node_dep_from   ON node_dependency(node_id);
CREATE INDEX idx_node_dep_to     ON node_dependency(depends_on_id);
CREATE INDEX idx_nse_latest      ON node_state_event(node_id, event_date DESC);

-- Session runtime
CREATE INDEX idx_state_tree      ON state(session_id, parent_state_id);
CREATE INDEX idx_task_queue      ON task(session_id, status, scheduled_date);
CREATE INDEX idx_request_queue   ON request(session_id, status, timeout_date);

-- Observer
CREATE INDEX idx_event_tail       ON event(session_id, sequence);
CREATE INDEX idx_dispatch_session ON dispatch(session_id, start_date);
CREATE INDEX idx_dispatch_agent   ON dispatch(agent_kind, agent_name);
CREATE INDEX idx_attempt_result   ON attempt(result_id, attempt_number);

-- plan_node_id cross-stream joins
CREATE INDEX idx_msg_node     ON message(plan_node_id);
CREATE INDEX idx_req_node     ON request(plan_node_id);
CREATE INDEX idx_event_node   ON event(plan_node_id);
CREATE INDEX idx_state_node   ON state(plan_node_id);
CREATE INDEX idx_result_node  ON result(plan_node_id);
CREATE INDEX idx_finding_node ON finding(plan_node_id);
