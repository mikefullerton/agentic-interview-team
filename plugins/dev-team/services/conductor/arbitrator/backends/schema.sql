-- Conductor arbitrator — SQLite schema
-- Resource tables from spec §6.1. Indexes from §6.3.
-- Keys: (session_id, team_id) on everything except `request` which has from/to.

CREATE TABLE IF NOT EXISTS session (
    session_id        TEXT PRIMARY KEY,
    initial_team_id   TEXT NOT NULL,
    status            TEXT NOT NULL,
    started_at        TEXT NOT NULL,
    ended_at          TEXT,
    metadata_json     TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS state (
    node_id           TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    team_id           TEXT NOT NULL,
    parent_node_id    TEXT,
    state_name        TEXT NOT NULL,
    status            TEXT NOT NULL,
    entered_at        TEXT NOT NULL,
    exited_at         TEXT,
    FOREIGN KEY (session_id) REFERENCES session(session_id)
);
CREATE INDEX IF NOT EXISTS idx_state_session_parent
    ON state(session_id, parent_node_id);

CREATE TABLE IF NOT EXISTS message (
    message_id        TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    team_id           TEXT NOT NULL,
    direction         TEXT NOT NULL,
    type              TEXT NOT NULL,
    body              TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES session(session_id)
);
CREATE INDEX IF NOT EXISTS idx_message_session_created
    ON message(session_id, created_at);

CREATE TABLE IF NOT EXISTS gate (
    gate_id           TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    team_id           TEXT NOT NULL,
    category          TEXT NOT NULL,
    options_json      TEXT NOT NULL,
    verdict           TEXT,
    created_at        TEXT NOT NULL,
    resolved_at       TEXT,
    FOREIGN KEY (session_id) REFERENCES session(session_id)
);

CREATE TABLE IF NOT EXISTS result (
    result_id         TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    team_id           TEXT NOT NULL,
    specialist_id     TEXT NOT NULL,
    passed            INTEGER NOT NULL,
    summary_json      TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES session(session_id)
);

CREATE TABLE IF NOT EXISTS finding (
    finding_id        TEXT PRIMARY KEY,
    result_id         TEXT NOT NULL,
    kind              TEXT NOT NULL,
    severity          TEXT NOT NULL,
    body              TEXT NOT NULL,
    source_artifact   TEXT,
    FOREIGN KEY (result_id) REFERENCES result(result_id)
);
CREATE INDEX IF NOT EXISTS idx_finding_result ON finding(result_id);

CREATE TABLE IF NOT EXISTS event (
    event_id          TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    team_id           TEXT,
    agent_id          TEXT,
    dispatch_id       TEXT,
    sequence          INTEGER NOT NULL,
    kind              TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    emitted_at        TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES session(session_id)
);
CREATE INDEX IF NOT EXISTS idx_event_session_sequence
    ON event(session_id, sequence);

CREATE TABLE IF NOT EXISTS task (
    task_id           TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    team_id           TEXT NOT NULL,
    kind              TEXT NOT NULL,
    payload_json      TEXT NOT NULL,
    status            TEXT NOT NULL,
    enqueued_at       TEXT NOT NULL,
    started_at        TEXT,
    completed_at      TEXT,
    result_json       TEXT,
    FOREIGN KEY (session_id) REFERENCES session(session_id)
);
CREATE INDEX IF NOT EXISTS idx_task_session_status_enqueued
    ON task(session_id, status, enqueued_at);

CREATE TABLE IF NOT EXISTS request (
    request_id        TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL,
    from_team         TEXT NOT NULL,
    to_team           TEXT NOT NULL,
    kind              TEXT NOT NULL,
    input_json        TEXT NOT NULL,
    status            TEXT NOT NULL,
    response_json     TEXT,
    parent_request_id TEXT,
    enqueued_at       TEXT NOT NULL,
    in_flight_at      TEXT,
    completed_at      TEXT,
    timeout_at        TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES session(session_id)
);
CREATE INDEX IF NOT EXISTS idx_request_session_status_enqueued
    ON request(session_id, status, enqueued_at);
