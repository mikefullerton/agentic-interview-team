---
name: input-validation
description: All validation duplicated server-side, allowlists over denylists, validate-sanitize-escape order, parameterized queries ...
artifact: guidelines/security/input-validation.md
version: 1.0.0
---

## Worker Focus
All validation duplicated server-side, allowlists over denylists, validate-sanitize-escape order, parameterized queries only, context-aware output encoding

## Verify
Server-side validation exists independent of client; parameterized queries used; output encoding is context-specific; no raw user input concatenated into queries/HTML
