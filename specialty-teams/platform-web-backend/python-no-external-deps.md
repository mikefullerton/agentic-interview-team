---
name: python-no-external-deps
description: Core library (`roadmap_lib`) uses standard library only — no PyYAML, requests, or other third-party packages; keeps libr...
artifact: guidelines/language/python/no-external-dependencies-in-core-librari.md
version: 1.0.0
---

## Worker Focus
Core library (`roadmap_lib`) uses standard library only — no PyYAML, requests, or other third-party packages; keeps library portable and pip-install-free

## Verify
`roadmap_lib` has no third-party imports; no `pip install` required for core library; standard library equivalents used (e.g., built-in YAML parser, `urllib` over `requests`)
