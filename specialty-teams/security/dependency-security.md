---
name: dependency-security
description: Lockfiles committed, CI audit step (npm audit/pip-audit/Dependabot) failing on critical/high, pinned versions (no wildca...
artifact: guidelines/security/dependency-security.md
version: 1.0.0
---

## Worker Focus
Lockfiles committed, CI audit step (npm audit/pip-audit/Dependabot) failing on critical/high, pinned versions (no wildcard), SRI on CDN assets

## Verify
Lockfile committed; audit step in CI config; no * version ranges; SRI integrity attributes on CDN script/style tags
