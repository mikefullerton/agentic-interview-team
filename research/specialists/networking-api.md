# Networking & API Specialist

## Role
REST conventions, HTTP semantics, offline-first, caching, retry/resilience, timeouts, pagination, real-time communication, error response format, rate limiting, API design conventions, and access-pattern compliance.

## Persona
(coming)

## Cookbook Sources
- `guidelines/networking/` (9 files — skip `references.md`, bibliography only)
- `principles/principle-of-least-astonishment.md`
- `compliance/access-patterns.md`

## Specialty Teams

### api-design
- **Artifact**: `guidelines/networking/api-design.md`
- **Worker focus**: REST with consistent URL conventions (lowercase-hyphen, plural nouns, max 2 nesting levels, no verbs, no trailing slashes), correct HTTP method semantics and idempotency, correct status codes, URL path versioning (`/v1/`) bumped only on breaking changes
- **Verify**: No verbs in URL paths; collections use plural nouns; HTTP methods match semantics table (POST→201+Location, DELETE→204, etc.); versioning present on all endpoints; no breaking changes without version bump

### error-responses
- **Artifact**: `guidelines/networking/error-responses.md`
- **Worker focus**: RFC 9457 Problem Details format with `Content-Type: application/problem+json`; required fields: `type` (URI), `title` (stable), `status` (mirrors HTTP), `detail` (occurrence-specific), `instance`; extension fields (`errors`, `trace_id`) for machine-readable details
- **Verify**: All error responses use `application/problem+json` content type; `type` field is a URI; `status` matches HTTP response code; field-level errors use `errors` array; no plain-string error bodies

### caching
- **Artifact**: `guidelines/networking/caching.md`
- **Worker focus**: Server controls cache policy via headers; immutable versioned assets use `public, max-age=31536000, immutable`; dynamic API responses use `private, max-age=N`; sensitive/mutation responses use `no-store`; ETags for conditional requests; post-mutation cache invalidation
- **Verify**: Immutable assets have long-lived `Cache-Control: immutable`; sensitive responses have `Cache-Control: no-store`; `ETag` headers present on cacheable resources; mutations invalidate related cache entries

### offline-and-connectivity
- **Artifact**: `guidelines/networking/offline-and-connectivity.md`
- **Worker focus**: Local-first with background sync for offline apps; three patterns in complexity order — optimistic updates (rollback on failure), queue-based sync (outbox drained on reconnect), conflict resolution (ETags/version numbers, 409 with both versions); track `last_synced_at`, show connectivity status, never silently discard user work
- **Verify**: Offline mutations go to an outbox queue rather than being discarded; connectivity status visible to user; failed sync items remain in queue for retry; conflict resolution strategy documented (server-wins, merge UI, or CRDT)

### pagination
- **Artifact**: `guidelines/networking/pagination.md`
- **Worker focus**: Cursor pagination preferred for most APIs — stable under concurrent mutations, consistent performance at any depth; offset pagination only when users need page numbers or data is static; response includes `next_cursor` + `has_more` (cursor) or `offset`/`limit`/`total` (offset)
- **Verify**: All collection endpoints return paginated responses (not unbounded lists); cursor-based pagination used unless offset explicitly justified; pagination envelope present with `has_more` or `total`

### rate-limiting
- **Artifact**: `guidelines/networking/rate-limiting.md`
- **Worker focus**: Honor `Retry-After` header on 429 responses; if no `Retry-After`, use exponential backoff; track `RateLimit-Remaining` proactively and slow down before hitting 429; queue and batch requests at the allowed rate rather than fire-and-retry
- **Verify**: 429 responses trigger retry with `Retry-After` delay; no retry storm on 429 (exponential backoff enforced); `RateLimit-Remaining` monitoring present or proactive throttling implemented

### real-time-communication
- **Artifact**: `guidelines/networking/real-time-communication.md`
- **Worker focus**: Start with SSE for server-push (built-in reconnection, standard HTTP, sufficient for 80%+ of real-time needs); WebSocket only when bidirectional streaming required; polling as fallback for very low frequency updates; reconnection with backoff required for persistent connections
- **Verify**: SSE used instead of WebSocket unless bidirectional streaming is required; reconnection logic present for SSE/WebSocket connections; reconnection uses backoff (not immediate retry loop)

### retry-and-resilience
- **Artifact**: `guidelines/networking/retry-and-resilience.md`
- **Worker focus**: Exponential backoff with full jitter (`random(0, min(max_delay, base * 2^attempt))`); base 1s, max cap 30s, 3-5 retries for idempotent, 0 for non-idempotent; retryable: 408/429/500(idempotent)/502/503/504; never retry 400/401/403/404/409/422; circuit breaker for cascading failure prevention
- **Verify**: Retry logic only applies to retryable status codes; non-idempotent requests not retried on 500; exponential backoff with jitter implemented (no fixed-interval retry); circuit breaker present or explicitly scoped out

### timeouts
- **Artifact**: `guidelines/networking/timeouts.md`
- **Worker focus**: Always set both connection timeout (10s) and read/response timeout (30s); total/request timeout 60-120s including retries; never use infinite timeouts; long-running operations use 202 Accepted + polling pattern instead of extended timeouts
- **Verify**: Connection timeout ≤10s configured; read timeout ≤30s configured; no requests with infinite (0/null) timeout; operations expected to take >30s return 202 Accepted with polling endpoint

### principle-of-least-astonishment
- **Artifact**: `principles/principle-of-least-astonishment.md`
- **Worker focus**: API and system behavior must match what callers expect; names must deliver exactly what they suggest; side effects must be obvious from the API signature; no surprise mutations on read endpoints, no silent state changes
- **Verify**: No GET endpoints with side effects; endpoint names accurately describe their behavior; idempotent methods (GET/PUT/DELETE) are actually idempotent; no undocumented implicit state changes

### access-patterns-compliance
- **Artifact**: `compliance/access-patterns.md`
- **Worker focus**: 8 compliance checks — api-design-conventions, offline-behavior, retry-with-backoff, timeout-configuration, rate-limit-handling, pagination-support, reconnection-strategy, error-response-handling
- **Verify**: Each compliance check has a status (passed/failed/partial/n-a) with evidence; timeout-configuration confirmed for all network requests; pagination-support confirmed for all collection endpoints; error-response-handling confirmed for all documented error codes

## Exploratory Prompts

1. If API latency doubled overnight, what breaks first? What brittle assumption are you making about response times?

2. Why does your app need offline? What's the actual user need — eventual consistency, local-first, or something else?

3. If the server rate-limited to 1 request per 10 seconds, how would your app behave? What would you redesign?

4. If you had to move from REST to GraphQL or gRPC, what's easier and harder? What's deeply tied to REST?
