# Web Frontend Platform Specialist

## Role
HTML/CSS/JS implementation of UI guidelines, accessibility (WCAG), responsive and adaptive layout, HTTP caching, CORS, CSP, networking patterns on the client, progressive enhancement, and offline behavior.

## Persona
(coming)

## Cookbook Sources
- `guidelines/ui/` (15 files)
- `guidelines/accessibility/accessibility.md`
- `guidelines/security/cors.md`
- `guidelines/security/content-security-policy.md`
- `guidelines/networking/` (9 files, excluding references.md)
- `compliance/platform-compliance.md`

## Specialty Teams

### always-show-progress
- **Artifact**: `guidelines/ui/always-show-progress.md`
- **Worker focus**: Implement determinate progress bars (with percentage) and indeterminate spinners/skeletons/shimmer in the DOM; prevent UI freeze during async operations
- **Verify**: No async operation leaves the DOM visually frozen; skeleton/shimmer uses CSS animations; progress bar updates as work completes

### animation-motion
- **Artifact**: `guidelines/ui/animation-motion.md`
- **Worker focus**: CSS transitions and JS animations use correct duration ranges per interaction type; `prefers-reduced-motion: reduce` media query disables/simplifies all animations; no continuous loops or large-distance motion
- **Verify**: `prefers-reduced-motion` media query handled in CSS; no `animation: infinite` without reduced-motion fallback; transition durations within specified ranges for interaction type

### color
- **Artifact**: `guidelines/ui/color.md`
- **Worker focus**: CSS custom properties (not hard-coded hex), semantic color tokens per design system, WCAG AA contrast ratios, `prefers-color-scheme` dark mode support, color never sole state indicator
- **Verify**: No raw hex values in component styles; color contrast ≥4.5:1 text, ≥3:1 large text/UI; `prefers-color-scheme: dark` handled; state changes always include non-color indicator

### data-display
- **Artifact**: `guidelines/ui/data-display.md`
- **Worker focus**: Implement correct HTML patterns — `<ul>/<li>` for lists, `<table>` with sortable columns for tabular data, card grid for heterogeneous browsable content; wire up sort/filter at 10+ items, search at 50+
- **Verify**: Tables rendered with `<th>` and sort controls; lists use semantic HTML; collections ≥10 have sort or filter; collections ≥50 have search input

### feedback-patterns
- **Artifact**: `guidelines/ui/feedback-patterns.md`
- **Worker focus**: Implement toast/snackbar (auto-dismiss 3-5s), inline alerts/banners, and modal dialogs; connect feedback weight to action weight; no `alert()` or dialogs for success; default focus on Cancel in destructive dialogs
- **Verify**: Toast auto-dismisses after 3-5s; success never triggers `window.alert()` or `<dialog>`; destructive dialogs use explicit labels (not "OK"); focus set to Cancel/safe button on dialog open

### form-design
- **Artifact**: `guidelines/ui/form-design.md`
- **Worker focus**: Single-column layout, `<label>` top-aligned or floating, blur-event validation (not input-event), submit-event full validation, inline error messages below field using ARIA (`aria-describedby`), pre-fill defaults, mark optional not required
- **Verify**: Validation triggered on blur not input; errors rendered inline below field; errors include icon + text (not color alone); `aria-describedby` links field to error; placeholder is not sole label

### iconography
- **Artifact**: `guidelines/ui/iconography.md`
- **Worker focus**: Use SVG icons with accessible names (`aria-label` or `<title>`), consistent size/weight classes, minimum 24x24px interactive, status icons paired with color + shape or text
- **Verify**: All icon buttons have `aria-label`; decorative icons have `aria-hidden="true"`; interactive icons ≥24x24px; status icons not color-only

### layout
- **Artifact**: `guidelines/ui/layout.md`
- **Worker focus**: CSS Grid/Flexbox with responsive breakpoints via media queries (no hard-coded widths); single-column default expanding to multi-column; no nested same-direction scroll; content-first element order
- **Verify**: No inline style pixel widths for layout; breakpoints use `em`/`rem` or device-class media queries; no nested overflow-y in overflow-y containers; DOM order matches visual reading order

### platform-design-languages
- **Artifact**: `guidelines/ui/platform-design-languages.md`
- **Worker focus**: Web target follows WCAG 2.1 and browser/OS design conventions; use platform-appropriate system font stack; fill gaps with cookbook defaults only where platform doesn't prescribe
- **Verify**: System font stack used (`system-ui, -apple-system, sans-serif`); WCAG 2.1 AA minimum followed; no custom design deviations without documented rationale

### spacing
- **Artifact**: `guidelines/ui/spacing.md`
- **Worker focus**: CSS custom properties or design tokens for spacing on 4px scale (4/8/12/16/24/32/48/64); no arbitrary values in margin/padding/gap; 16px content edge padding
- **Verify**: No spacing values off the 4px scale in computed styles; CSS variables used for spacing tokens; no `5px`, `13px`, or similar arbitrary values

### state-design
- **Artifact**: `guidelines/ui/state-design.md`
- **Worker focus**: Implement all four states in component templates — loading (skeleton/spinner), empty (illustration + message + CTA button), error (message + retry/back action), loaded; never render blank DOM with no explanation
- **Verify**: All four states render for every data-loading component; empty state has visible CTA; error state has retry or navigation action; no raw error codes or stack traces in DOM

### touch-click-targets
- **Artifact**: `guidelines/ui/touch-click-targets.md`
- **Worker focus**: Web minimum 24x24 CSS px (target 44x44), pad hit area beyond visual element via padding, ≥8px gap between adjacent targets; WCAG 2.5.8 compliance
- **Verify**: Interactive elements computed size ≥24x24 CSS px; adjacent targets ≥8px apart; buttons/links have sufficient padding beyond icon/text visual

### typography
- **Artifact**: `guidelines/ui/typography.md`
- **Worker focus**: System font stack, body 16px default, minimum 11-12px captions, line-height 1.4-1.5x, 2-3 weights per screen, paragraph max-width 45-75ch, `prefers-reduced-data` reduces font loading
- **Verify**: System font stack in CSS; body `font-size` ≥14px; no element `font-size` <11px; `line-height` ≥1.4 on body text; paragraph `max-width` ≤75ch

### visual-hierarchy
- **Artifact**: `guidelines/ui/visual-hierarchy.md`
- **Worker focus**: Single primary CTA per screen with `type="submit"` or strong visual weight; heading hierarchy via `<h1>`–`<h6>` and font size/weight; interactive vs. static elements visually distinct; disabled state via `disabled` attribute + CSS
- **Verify**: One primary action per screen; heading tags used in order; `<button>` vs. `<span>` used correctly for interactive vs. static; `disabled` attribute set on inactive controls

### accessibility
- **Artifact**: `guidelines/accessibility/accessibility.md`
- **Worker focus**: WCAG 2.1 AA minimum; ARIA roles, states, properties (WAI-ARIA APG); keyboard navigation for all interactive elements; `aria-live` for dynamic content; focus order following visual layout; CSS media queries for reduced-motion, high-contrast, forced-colors, dark mode, reduced-transparency
- **Verify**: All interactive elements keyboard-reachable and operable with Enter/Space; `aria-live` on dynamic update regions; focus order follows visual layout; `prefers-reduced-motion` handled; contrast ratios pass 4.5:1 text / 3:1 large

### cors
- **Artifact**: `guidelines/security/cors.md`
- **Worker focus**: Never reflect Origin header; static allowlist of permitted origins; no wildcard with credentials; `Access-Control-Max-Age: 86400`; no `null` origin; anchored regex if dynamic matching required
- **Verify**: CORS config uses static allowlist or anchored regex; no `Access-Control-Allow-Origin: *` with credentials; preflight `Access-Control-Max-Age` set; `null` origin not in allowlist

### content-security-policy
- **Artifact**: `guidelines/security/content-security-policy.md`
- **Worker focus**: Implement `default-src 'none'` baseline, nonce-based script-src with strict-dynamic, no `unsafe-inline`/`unsafe-eval`, `frame-ancestors 'self'`; deploy in report-only mode first
- **Verify**: CSP header present; no `unsafe-inline` or `unsafe-eval` in script-src; nonce rotated per request; `frame-ancestors 'self'` set; no third-party domain in script-src without justification

### api-design-client
- **Artifact**: `guidelines/networking/api-design.md`
- **Worker focus**: Client calls match REST conventions — correct HTTP methods, no verb-in-URL, proper status code handling (201 for create, 204 for delete, 422 for validation); URL path versioning respected
- **Verify**: Client uses GET for reads, POST for creates, DELETE for removes; 201 responses extract Location header; 422 responses display field-level errors; client handles versioned URL paths

### caching
- **Artifact**: `guidelines/networking/caching.md`
- **Worker focus**: Immutable versioned assets use `Cache-Control: public, max-age=31536000, immutable`; sensitive data uses `no-store`; ETag conditional requests for revalidation; client-side cache invalidated after mutations
- **Verify**: Versioned JS/CSS/images have immutable Cache-Control; auth/session responses have no-store; ETag/If-None-Match flow implemented for dynamic content; mutations trigger cache invalidation

### error-responses-client
- **Artifact**: `guidelines/networking/error-responses.md`
- **Worker focus**: Parse RFC 9457 Problem Details (`application/problem+json`); display `detail` field to user; surface `errors[]` field for field-level validation; include `instance`/`trace_id` in error reports
- **Verify**: Client parses `application/problem+json`; field errors from `errors[]` shown inline; no raw status codes shown to user; error UI includes recovery action

### offline-and-connectivity
- **Artifact**: `guidelines/networking/offline-and-connectivity.md`
- **Worker focus**: Optimistic updates for most cases; outbox queue for mutations during offline; clear connectivity status indicator; no silent discard of user work; Service Worker for offline asset serving if needed
- **Verify**: Connectivity status shown to user; mutations queued when offline and retried on reconnect; no user-initiated action silently discarded; optimistic update rolled back on server failure

### pagination-client
- **Artifact**: `guidelines/networking/pagination.md`
- **Worker focus**: Client handles cursor-based pagination (`next_cursor`, `has_more`) and offset-based; infinite scroll or "Load more" for cursor; page controls for offset; no full re-fetch on page change
- **Verify**: Pagination response shape parsed correctly; `has_more: false` hides load-more trigger; cursor stored and sent on next page request; loading state shown between pages

### rate-limiting-client
- **Artifact**: `guidelines/networking/rate-limiting.md`
- **Worker focus**: Honor `Retry-After` header on 429; track `RateLimit-Remaining` and throttle proactively; queue/batch requests at allowed rate; never fire-and-retry in a loop
- **Verify**: 429 response triggers wait using `Retry-After`; no tight retry loops without backoff; client reads `RateLimit-Remaining` if available

### real-time-communication
- **Artifact**: `guidelines/networking/real-time-communication.md`
- **Worker focus**: Prefer SSE (`EventSource`) for server-push (notifications, live feeds, progress); WebSocket only for bidirectional streaming; SSE has built-in reconnection; polling as low-frequency fallback
- **Verify**: SSE used for unidirectional push; WebSocket only where bidirectional required and justified; EventSource reconnection not suppressed; polling interval ≥1min if used

### retry-and-resilience-client
- **Artifact**: `guidelines/networking/retry-and-resilience.md`
- **Worker focus**: Exponential backoff with full jitter for transient failures (408, 429, 500, 502, 503, 504); max 3-5 retries for idempotent, 0 for non-idempotent; never retry 400/401/403/404/422; circuit breaker for cascading failures
- **Verify**: Retry logic only on retryable status codes; non-idempotent requests (POST) not retried by default; backoff includes jitter; circuit breaker or similar prevents cascading

### timeouts-client
- **Artifact**: `guidelines/networking/timeouts.md`
- **Worker focus**: All fetch/XHR calls have connection timeout (10s), response timeout (30s), total lifecycle timeout (60-120s); no infinite-wait fetch; long-running ops use 202 Accepted + polling
- **Verify**: `AbortController` or equivalent timeout set on all network requests; no `fetch()` without timeout; long-running endpoints use polling not extended timeout

### platform-compliance
- **Artifact**: `compliance/platform-compliance.md`
- **Worker focus**: Web platform: WCAG 2.1 AA design language, native browser controls preferred, WCAG touch targets, dark mode and forced-colors theming, minimum permissions requested
- **Verify**: platform-design-language (WCAG/browser conventions), platform-touch-targets (24px min web), platform-theming (dark mode + forced-colors) checks each have status with evidence

## Exploratory Prompts

1. If JavaScript was disabled, what would your app show? Is progressive enhancement important for your use case?

2. What if your target audience is primarily on mobile browsers with slow connections? How would that change your architecture?

3. How do you handle the tension between rich interactivity and page load performance?

4. If you had to support a screen reader perfectly, which component in your app would be hardest to make accessible?
