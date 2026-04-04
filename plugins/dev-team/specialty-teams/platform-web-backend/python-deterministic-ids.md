---
name: python-deterministic-ids
description: IDs taken from YAML frontmatter UUID, never `uuid.uuid4()` or random generation; IDs must be reproducible across runs
artifact: guidelines/language/python/deterministic-ids.md
version: 1.0.0
---

## Worker Focus
IDs taken from YAML frontmatter UUID, never `uuid.uuid4()` or random generation; IDs must be reproducible across runs

## Verify
No `uuid.uuid4()` or `random` calls for ID generation; IDs sourced from frontmatter `id` field; same input always produces same ID
