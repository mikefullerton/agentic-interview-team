---
id: 2FF8FEE9-3EAC-4CF3-9B0E-F88BD3CAFF58
title: "Access Patterns"
domain: agentic-cookbook://compliance/access-patterns
type: compliance
version: 1.0.0
status: draft
language: en
created: 2026-03-28
modified: 2026-03-28
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Compliance checks for network communication, API design, and data access patterns."
platforms: []
tags: [compliance, access-patterns]
depends-on: []
related:
  - agentic-cookbook://compliance/reliability
  - agentic-cookbook://compliance/performance
  - agentic-cookbook://compliance/security
references: []
---

# Access Patterns

Compliance checks that govern how components communicate over the network, design their APIs, and handle the inherent unreliability of distributed access. These checks ensure consistent, resilient, and well-behaved network interactions across all platforms.

## Applicability

Recipes or guidelines involving network communication, API calls, data synchronization, or client-server interaction.

## Checks

### api-design-conventions

APIs MUST follow RESTful conventions with consistent naming and versioning.

**Applies when:** a component exposes or consumes an HTTP API.

**Guidelines:**
- [API Design](agentic-cookbook://guidelines/networking/api-design)

---

### offline-behavior

Components MUST define behavior when network is unavailable.

**Applies when:** a feature depends on network connectivity to function.

**Guidelines:**
- [Offline and Connectivity](agentic-cookbook://guidelines/networking/offline-and-connectivity)

---

### retry-with-backoff

Failed network requests MUST implement retry with exponential backoff and jitter.

**Applies when:** a component makes network requests that may transiently fail.

**Guidelines:**
- [Retry and Resilience](agentic-cookbook://guidelines/networking/retry-and-resilience)

---

### timeout-configuration

All network requests MUST have configured timeouts; MUST NOT wait indefinitely.

**Applies when:** a component initiates any network request.

**Guidelines:**
- [Timeouts](agentic-cookbook://guidelines/networking/timeouts)

---

### rate-limit-handling

Clients MUST handle HTTP 429 responses and respect Retry-After headers.

**Applies when:** a component calls rate-limited APIs or services.

**Guidelines:**
- [Rate Limiting](agentic-cookbook://guidelines/networking/rate-limiting)

---

### pagination-support

Endpoints returning collections MUST support pagination.

**Applies when:** an API endpoint returns a list of resources.

**Guidelines:**
- [Pagination](agentic-cookbook://guidelines/networking/pagination)

---

### reconnection-strategy

Real-time connections MUST define reconnection behavior with backoff.

**Applies when:** a component uses WebSockets, server-sent events, or other persistent connections.

**Guidelines:**
- [Real-Time Communication](agentic-cookbook://guidelines/networking/real-time-communication)

---

### error-response-handling

Clients MUST handle all documented error response codes gracefully.

**Applies when:** a component consumes an API that defines error responses.

**Guidelines:**
- [Error Responses](agentic-cookbook://guidelines/networking/error-responses)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-28 | Mike Fullerton | Initial creation |
