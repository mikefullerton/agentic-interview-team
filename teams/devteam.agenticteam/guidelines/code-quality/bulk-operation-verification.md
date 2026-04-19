---

id: b4e8d2c3-9f5a-4b0e-c7d4-3e2f1a0b9c8d
title: "Bulk operation verification"
domain: agentic-cookbook://guidelines/reviewing/code-quality/bulk-operation-verification
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-28
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "After any operation touching 5+ files, run a verification pass for stale references before marking complete."
platforms: []
tags:
  - bulk-operations
  - verification
  - code-quality
depends-on:
  - agentic-cookbook://guidelines/code-quality/atomic-commits
related:
  - agentic-cookbook://guidelines/testing/post-generation-verification
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - code-review
  - pre-commit
---

# Bulk operation verification

Any operation that touches more than 5 files — renames, migrations, restructurings, bulk updates — MUST have a verification pass before the task is considered complete.

## What to verify

After the bulk operation finishes:

1. **Stale references**: The entire repo MUST be grepped for old names, paths, or identifiers that should have been updated. Check source code, documentation, configuration files, indexes, skills, rules, and test fixtures.

2. **Cross-reference integrity**: Verify that every file that references a renamed/moved entity has been updated. Common miss points:
   - README and CLAUDE.md
   - Index files and tables of contents
   - Import statements and require paths
   - Skill files that reference other skills by name
   - Rule files that reference skills or other rules
   - CI/CD configuration
   - Symlinks

3. **Completeness**: Confirm the operation covered all intended files. List what was changed and compare against what should have been changed.

## When to run

- After any rename (files, directories, functions, variables across files)
- After migrating content between directories or repos
- After restructuring a directory layout
- After updating a convention across multiple files (e.g., frontmatter format)

## For cross-repo operations

Verify each repo independently. Then run a cross-repo check to confirm consistency — the same identifier should resolve correctly in every repo that references it.

## The rule

A bulk operation MUST NOT be marked complete until the verification pass returns zero stale references.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-28 | Mike Fullerton | Initial creation |
