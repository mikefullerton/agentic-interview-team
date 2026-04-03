-- Dev-team database schema v2
-- DB-centric architecture with formalized terminology

-- Sessions: a workflow run
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    playbook TEXT NOT NULL,
    team_lead TEXT NOT NULL,
    user TEXT NOT NULL,
    machine TEXT NOT NULL
);

-- Paths: flexible path storage for any table
CREATE TABLE paths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(id),
    path TEXT NOT NULL,
    type TEXT NOT NULL
);

-- Session state: append-only state transitions
CREATE TABLE session_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT NOT NULL,
    specialist TEXT,
    state TEXT NOT NULL,
    description TEXT
);

-- Retries: why something was retried
CREATE TABLE retries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    session_state_id INTEGER NOT NULL REFERENCES session_state(id),
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reason TEXT NOT NULL
);

-- Results: one specialist's output for a session
CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    specialist TEXT NOT NULL
);

-- Findings: individual issues within a result
CREATE TABLE findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL REFERENCES results(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    specialist TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    detail TEXT NOT NULL
);

-- Interpretations: persona translations of findings (written in a later step)
CREATE TABLE interpretations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_id INTEGER NOT NULL REFERENCES findings(id),
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    specialist TEXT NOT NULL,
    interpretation TEXT NOT NULL
);

-- Artifacts: cookbook artifacts referenced by other entities
CREATE TABLE artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    artifact TEXT NOT NULL,
    message TEXT,
    description TEXT
);

-- Join tables: link artifacts to the entities that reference them
CREATE TABLE finding_artifacts (
    finding_id INTEGER NOT NULL REFERENCES findings(id),
    artifact_id INTEGER NOT NULL REFERENCES artifacts(id),
    PRIMARY KEY (finding_id, artifact_id)
);

CREATE TABLE session_state_artifacts (
    session_state_id INTEGER NOT NULL REFERENCES session_state(id),
    artifact_id INTEGER NOT NULL REFERENCES artifacts(id),
    PRIMARY KEY (session_state_id, artifact_id)
);

-- Messages: team-lead <-> user interaction
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    type TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    specialist TEXT,
    content TEXT NOT NULL,
    category TEXT,
    severity TEXT
);

-- Gate options: choices for gate-type messages
CREATE TABLE gate_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL REFERENCES messages(id),
    option_text TEXT NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL
);
