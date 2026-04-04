-- Dev-team shared database schema v2

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  path TEXT NOT NULL,
  status TEXT DEFAULT 'active',
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  workflow TEXT NOT NULL,
  status TEXT DEFAULT 'running',
  started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session_state (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL REFERENCES sessions(id),
  agent_type TEXT NOT NULL,
  specialist_domain TEXT,
  status TEXT DEFAULT 'running',
  started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed TIMESTAMP,
  output_path TEXT
);

CREATE TABLE IF NOT EXISTS findings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_state_id INTEGER REFERENCES session_state(id),
  project_id INTEGER NOT NULL REFERENCES projects(id),
  type TEXT NOT NULL,
  severity TEXT,
  description TEXT NOT NULL,
  artifact_path TEXT,
  status TEXT DEFAULT 'open',
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requirements (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  recipe_path TEXT NOT NULL,
  text TEXT NOT NULL,
  keyword TEXT NOT NULL,
  covered_by_baseline TEXT,
  covered_by_target TEXT
);

CREATE TABLE IF NOT EXISTS comparisons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  session_id INTEGER REFERENCES sessions(id),
  baseline_path TEXT NOT NULL,
  target_path TEXT NOT NULL,
  preservation_pct REAL,
  regressions_count INTEGER DEFAULT 0,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS specialist_assignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  session_id INTEGER REFERENCES sessions(id),
  recipe_path TEXT NOT NULL,
  specialist TEXT NOT NULL,
  tier INTEGER,
  approved INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS screenshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  comparison_id INTEGER NOT NULL REFERENCES comparisons(id),
  name TEXT NOT NULL,
  similarity_pct REAL,
  baseline_path TEXT,
  target_path TEXT,
  diff_path TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER REFERENCES projects(id),
  session_id INTEGER REFERENCES sessions(id),
  session_state_id INTEGER REFERENCES session_state(id),
  path TEXT,
  relative_path TEXT,
  category TEXT NOT NULL,
  title TEXT,
  specialist TEXT,
  frontmatter_json TEXT,
  content TEXT,
  content_hash TEXT,
  version INTEGER DEFAULT 1,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER REFERENCES sessions(id),
  session_state_id INTEGER REFERENCES session_state(id),
  agent_type TEXT,
  specialist_domain TEXT,
  persona TEXT,
  message TEXT NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id, workflow);
CREATE INDEX IF NOT EXISTS idx_session_state_session ON session_state(session_id);
CREATE INDEX IF NOT EXISTS idx_findings_project ON findings(project_id, type, status);
CREATE INDEX IF NOT EXISTS idx_artifacts_project ON artifacts(project_id, category);
CREATE INDEX IF NOT EXISTS idx_messages_run ON messages(session_id);
