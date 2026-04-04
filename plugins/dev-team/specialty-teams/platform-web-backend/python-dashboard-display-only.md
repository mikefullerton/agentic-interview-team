---
name: python-dashboard-display-only
description: Dashboard service is a generic display layer — no git, file, or roadmap-structure knowledge; agents push data to it; it ...
artifact: guidelines/language/python/dashboard-service-is-display-only.md
version: 1.0.0
---

## Worker Focus
Dashboard service is a generic display layer — no git, file, or roadmap-structure knowledge; agents push data to it; it only renders what it receives

## Verify
Dashboard service contains no `git` commands, no file I/O of roadmap files, no frontmatter parsing; all data arrives via API from agents
