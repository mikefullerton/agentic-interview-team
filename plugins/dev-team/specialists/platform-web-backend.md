# Web Backend / Services Platform Specialist

## Role
API design, networking resilience (retry, timeouts, rate limiting, real-time), security (CORS, CSP, input validation, transport, auth), Python language conventions, and backend reliability and access-pattern compliance.

## Persona
(coming)

## Cookbook Sources
- `guidelines/networking/` (9 files, excluding references.md)
- `guidelines/security/cors.md`
- `guidelines/security/content-security-policy.md`
- `guidelines/language/python/` (10 files)
- `compliance/reliability.md`
- `compliance/access-patterns.md`
- `compliance/security.md`

## Specialty Teams

### api-design
- **Artifact**: `guidelines/networking/api-design.md`
- **Worker focus**: REST conventions — lowercase-hyphenated plural-noun URLs, max 2-level nesting, no verbs in URLs, correct HTTP methods with idempotency, right status codes (201+Location for POST, 204 for DELETE, 409 for conflict, 422 for validation), URL-path versioning
- **Verify**: No verbs in URL paths; collections are plural nouns; POST returns 201 with Location header; DELETE returns 204; 422 used for validation errors (not 400); version in URL path (`/v1/...`)

### caching
- **Artifact**: `guidelines/networking/caching.md`
- **Worker focus**: Server sets correct Cache-Control — immutable for versioned assets, `private, max-age=N` for dynamic, `no-store` for sensitive/mutations; ETag/If-None-Match support; never cache credentials or PII
- **Verify**: Sensitive endpoints have `Cache-Control: no-store`; versioned static assets have `max-age=31536000, immutable`; ETag header set on cacheable responses; mutations do not have a positive max-age

### error-responses
- **Artifact**: `guidelines/networking/error-responses.md`
- **Worker focus**: RFC 9457 Problem Details format with `Content-Type: application/problem+json`; machine-readable `type` URI, stable `title`, mirrored `status`, occurrence-specific `detail`, `instance`, and extension fields (`errors[]`, `trace_id`)
- **Verify**: All error responses use `application/problem+json`; `type` is a URI; `status` mirrors HTTP status code; `errors[]` present for validation failures with field-level messages; no stack traces in response body

### offline-and-connectivity
- **Artifact**: `guidelines/networking/offline-and-connectivity.md`
- **Worker focus**: Server supports ETag/version numbers for conflict detection (409 with both versions); delta sync via `last_synced_at`; outbox queue patterns on client enabled by server returning reliable mutation acknowledgment
- **Verify**: Conflict scenarios return 409 with current server state; ETag or version field on mutable resources; delta sync endpoints accept `since` parameter

### pagination
- **Artifact**: `guidelines/networking/pagination.md`
- **Worker focus**: Cursor pagination by default (`next_cursor`, `has_more`) for most APIs; offset (`offset`, `limit`, `total`) only when page numbers required or data is static; consistent response envelope
- **Verify**: All collection endpoints paginated; cursor response includes `next_cursor` and `has_more`; offset response includes `total`; no unbounded list endpoints returning all records

### rate-limiting
- **Artifact**: `guidelines/networking/rate-limiting.md`
- **Worker focus**: Emit `Retry-After` header on 429 responses; expose `RateLimit-Remaining`/`RateLimit-Reset` headers proactively; apply per-client rate limits; queue-friendly (batching preferred over fire-and-retry)
- **Verify**: 429 responses include `Retry-After` header; `RateLimit-Remaining` emitted on responses to rate-limited routes; rate limits applied per API key or authenticated user

### real-time-communication
- **Artifact**: `guidelines/networking/real-time-communication.md`
- **Worker focus**: SSE endpoints for server-push (notifications, live feeds, progress); WebSocket only for bidirectional streaming; SSE uses standard `text/event-stream` with reconnection semantics; polling endpoints available as fallback
- **Verify**: SSE endpoint uses `Content-Type: text/event-stream`; Last-Event-ID reconnection supported; WebSocket upgrade only where bidirectional justified; long-polling not used where SSE suffices

### retry-and-resilience
- **Artifact**: `guidelines/networking/retry-and-resilience.md`
- **Worker focus**: Idempotent endpoints (GET, PUT, DELETE) safe to retry; POST endpoints idempotency keys where needed; server-side circuit breaker for upstream dependencies; 503 includes `Retry-After`
- **Verify**: GET/PUT/DELETE are idempotent as implemented; 503 responses include `Retry-After`; upstream dependency failures return 503 (not 500); circuit breaker state logged

### timeouts
- **Artifact**: `guidelines/networking/timeouts.md`
- **Worker focus**: All outbound HTTP calls have connection timeout (10s), read timeout (30s), total lifecycle timeout (60-120s); long-running operations use 202 Accepted + status polling endpoint; no infinite-wait calls to downstream services
- **Verify**: All `requests`/`httpx`/similar calls have `timeout=` set; no `timeout=None`; long-running tasks return 202 with status URL; no blocking calls without upper bound

### cors
- **Artifact**: `guidelines/security/cors.md`
- **Worker focus**: Explicit static allowlist of origins, never reflect Origin, no wildcard with credentials, `Access-Control-Max-Age: 86400`, no `null` origin, anchored regex for any dynamic matching
- **Verify**: CORS config is a static list or anchored regex; no `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`; `null` not in allowlist; preflight Max-Age set

### content-security-policy
- **Artifact**: `guidelines/security/content-security-policy.md`
- **Worker focus**: Server sets CSP header on all HTML responses; `default-src 'none'` baseline; nonce-based `script-src` with `strict-dynamic`; no `unsafe-inline`/`unsafe-eval`; `frame-ancestors 'self'`; report-only mode first
- **Verify**: CSP header present on HTML responses; no `unsafe-inline` or `unsafe-eval` in script-src; nonce generated per-request; `frame-ancestors 'self'` present

### python-database
- **Artifact**: `guidelines/language/python/database.md`
- **Worker focus**: SQLite with WAL mode (`PRAGMA journal_mode=WAL`), `sqlite3` standard library (no ORM), direct SQL queries
- **Verify**: WAL mode pragma set on connection; no SQLAlchemy or ORM import; `sqlite3` module used directly; parameterized queries only (no string concatenation)

### python-deterministic-ids
- **Artifact**: `guidelines/language/python/deterministic-ids.md`
- **Worker focus**: IDs taken from YAML frontmatter UUID, never `uuid.uuid4()` or random generation; IDs must be reproducible across runs
- **Verify**: No `uuid.uuid4()` or `random` calls for ID generation; IDs sourced from frontmatter `id` field; same input always produces same ID

### python-file-paths
- **Artifact**: `guidelines/language/python/file-paths.md`
- **Worker focus**: `pathlib.Path` for all path operations, never `os.path` string concatenation; `Path.home()` for home-relative paths
- **Verify**: No `os.path.join`, `os.path.exists`, or string `/` path concatenation; all path operations use `pathlib.Path`; imports include `from pathlib import Path`

### python-no-external-deps
- **Artifact**: `guidelines/language/python/no-external-dependencies-in-core-librari.md`
- **Worker focus**: Core library (`roadmap_lib`) uses standard library only — no PyYAML, requests, or other third-party packages; keeps library portable and pip-install-free
- **Verify**: `roadmap_lib` has no third-party imports; no `pip install` required for core library; standard library equivalents used (e.g., built-in YAML parser, `urllib` over `requests`)

### python-shell-scripts
- **Artifact**: `guidelines/language/python/shell-scripts.md`
- **Worker focus**: `main()` functions delegate to named functions — no inline logic in main; composable and testable structure
- **Verify**: `main()` body contains only function calls; no inline if/for/try blocks in main; each logical step is a named function

### python-type-hints
- **Artifact**: `guidelines/language/python/type-hints.md`
- **Worker focus**: Type hints welcome but not required; Python 3.9 compatibility — use `from __future__ import annotations` or `typing` module forms; avoid `list[str]` syntax without `__future__` import
- **Verify**: No 3.10+ syntax without compatibility guard; `from __future__ import annotations` present if modern syntax used; `Optional[str]` or `str | None` (with guard) used correctly

### python-use-roadmaplib
- **Artifact**: `guidelines/language/python/use-roadmaplib.md`
- **Worker focus**: Use `roadmap_lib` functions for all roadmap operations (reading state, parsing frontmatter, finding steps); never reimplement what already exists in the library
- **Verify**: No duplicate implementations of frontmatter parsing, state reading, or step finding; `roadmap_lib` imported and used for roadmap operations

### python-web-services
- **Artifact**: `guidelines/language/python/web-services.md`
- **Worker focus**: Flask for web services; REST API with SSE or polling for live updates; no other web frameworks
- **Verify**: `Flask` imported for any HTTP service; no FastAPI, Django, or other frameworks; SSE or polling used for live update endpoints

### python-yaml-frontmatter
- **Artifact**: `guidelines/language/python/yaml-frontmatter.md`
- **Worker focus**: Use `roadmap_lib`'s built-in frontmatter parser for `---` delimited frontmatter; no PyYAML dependency
- **Verify**: No `import yaml` or `PyYAML` dependency; frontmatter parsed via `roadmap_lib`; `---` delimiters handled correctly

### python-dashboard-display-only
- **Artifact**: `guidelines/language/python/dashboard-service-is-display-only.md`
- **Worker focus**: Dashboard service is a generic display layer — no git, file, or roadmap-structure knowledge; agents push data to it; it only renders what it receives
- **Verify**: Dashboard service contains no `git` commands, no file I/O of roadmap files, no frontmatter parsing; all data arrives via API from agents

### reliability-compliance
- **Artifact**: `compliance/reliability.md`
- **Worker focus**: 8 compliance checks — error-recovery (retry transient failures), graceful-degradation (handle unavailable dependencies), fault-tolerance (no crash on unexpected input), state-recovery (restore after restart), idempotent-operations, timeout-handling (consistent state after timeout), data-integrity, health-observability
- **Verify**: Each check has status (passed/failed/partial/n-a) with evidence; timeout handling leaves no dangling locks or partial writes; idempotent endpoints verified as safe to retry

### access-patterns-compliance
- **Artifact**: `compliance/access-patterns.md`
- **Worker focus**: 8 compliance checks — api-design-conventions, offline-behavior, retry-with-backoff, timeout-configuration, rate-limit-handling, pagination-support, reconnection-strategy, error-response-handling
- **Verify**: Each check has status with evidence; all collection endpoints paginated; all outbound calls have timeouts; 429 handling with Retry-After documented

### security-compliance
- **Artifact**: `compliance/security.md`
- **Worker focus**: 12 compliance checks — secure-authentication (OAuth/PKCE), server-side-authorization, secure-storage, input-sanitization, secure-transport (TLS 1.2+), secure-log-output (no PII/tokens), token-lifecycle, dependency-scanning, security-headers, content-security-policy, cors-allowlist, security-testing
- **Verify**: Each check has status with evidence; no PII in logs confirmed; token expiry ≤15min verified; dependency scan in CI; all 7 security headers present

## Exploratory Prompts

1. If your primary database went down for an hour, what happens? Can users still do anything?

2. What if traffic 10x'd overnight? What breaks first? What's your bottleneck?

3. Why monolith / why microservices? What would make you switch?

4. If you had to explain your backend to a new hire in 5 minutes, where would you start? What's the hardest thing to understand?
