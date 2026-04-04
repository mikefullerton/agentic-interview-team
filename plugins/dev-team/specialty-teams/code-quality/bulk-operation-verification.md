---
name: bulk-operation-verification
description: After any operation touching 5+ files, run a verification pass; grep entire repo for stale references (old names, paths,...
artifact: guidelines/code-quality/bulk-operation-verification.md
version: 1.0.0
---

## Worker Focus
After any operation touching 5+ files, run a verification pass; grep entire repo for stale references (old names, paths, identifiers); check source, docs, config, indexes, skills, rules, CI/CD, symlinks; verify cross-repo consistency for cross-repo operations

## Verify
Zero stale references remaining after bulk operation; README/CLAUDE.md updated; import paths updated; CI/CD config updated; symlinks valid
