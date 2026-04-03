# Database Platform Specialist

## Role
Schema design, migrations, indexing, query optimization, geoscaling, failover, replication, backup/restore, data modeling.

## Persona
(coming)

## Cookbook Sources
- `guidelines/language/python/database.md`
- `compliance/reliability.md`
- `compliance/access-patterns.md`

## Specialty Teams

### database
- **Artifact**: `guidelines/language/python/database.md`
- **Worker focus**: SQLite with WAL mode for concurrent read access; no ORM — direct SQL via `sqlite3` standard library; `PRAGMA journal_mode=WAL` set on connection open
- **Verify**: `PRAGMA journal_mode=WAL` present in connection setup; no ORM imports (SQLAlchemy, Django ORM, etc.); raw `sqlite3` module used for all queries

### reliability-compliance
- **Artifact**: `compliance/reliability.md`
- **Worker focus**: 8 compliance checks — error-recovery (transient error handling with retry), graceful-degradation (unavailable dependency fallback), fault-tolerance (no crashes on unexpected input), state-recovery (persistent state survives restart), idempotent-operations (safe retries), timeout-handling (consistent state after timeout), data-integrity (corrupt data detected and reported), health-observability (long-running services emit health metrics)
- **Verify**: Each compliance check has a status (passed/failed/partial/n-a) with evidence; retry logic present for network/IO calls; no operations that wait indefinitely without a timeout; state can be restored after process kill and restart

### access-patterns-compliance
- **Artifact**: `compliance/access-patterns.md`
- **Worker focus**: 8 compliance checks — api-design-conventions (RESTful with versioning), offline-behavior (defined behavior when network unavailable), retry-with-backoff (exponential backoff + jitter on failure), timeout-configuration (no indefinite waits), rate-limit-handling (HTTP 429 + Retry-After respected), pagination-support (collection endpoints paginated), reconnection-strategy (WebSocket/SSE reconnect with backoff), error-response-handling (all documented error codes handled)
- **Verify**: Each compliance check has a status with evidence; retry implementation uses exponential backoff with jitter; all network calls have explicit timeouts; HTTP 429 handling present if rate-limited APIs are consumed

## Exploratory Prompts

1. If your data model had to support a feature you haven't thought of yet, where would the pain be? What's inflexible?

2. What if you needed to change your primary database technology? What's tightly coupled?

3. If you had to guarantee zero data loss across regions during a network partition, what would you trade off?

4. What's the relationship between your data model and your domain model? Are they the same thing?
