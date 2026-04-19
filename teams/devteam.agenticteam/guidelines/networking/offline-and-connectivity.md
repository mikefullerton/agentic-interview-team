---

id: 67c59594-a5dc-46f2-aa61-3436921294c7
title: "Offline and Connectivity"
domain: agentic-cookbook://guidelines/implementing/networking/offline-and-connectivity
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "For apps that must work offline, design for local-first with background sync."
platforms: 
  - web
tags: 
  - networking
  - offline-and-connectivity
depends-on: []
related: []
references: 
  - https://crdt.tech/
  - https://web.dev/articles/offline-cookbook
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - offline-support
  - networking
---

# Offline and Connectivity

For apps that must work offline, design for local-first with background sync.

**Patterns (in order of complexity):**
1. **Optimistic updates** — apply changes to local UI immediately, sync in background. Roll
   back on server failure. Sufficient for most apps.
2. **Queue-based sync** — mutations go into an outbox queue, drained when connectivity returns.
   Failed items stay in queue for retry.
3. **Conflict resolution** — use ETags or version numbers to detect conflicts. Return 409 with
   both versions. Simple apps use server-wins; collaborative apps need merge UI or CRDTs.

**Practical defaults:**
- Track `last_synced_at` per entity for delta sync
- Show clear connectivity status to the user
- Mutations MUST be queued locally; user work MUST NOT be silently discarded
- Offline scenarios SHOULD be tested — airplane mode, flaky connections, long offline periods

References:
- [web.dev: Offline Cookbook](https://web.dev/articles/offline-cookbook)
- [CRDTs](https://crdt.tech/)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
