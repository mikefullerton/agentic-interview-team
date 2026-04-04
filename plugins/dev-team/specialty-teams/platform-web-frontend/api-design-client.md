---
name: api-design-client
description: Client calls match REST conventions — correct HTTP methods, no verb-in-URL, proper status code handling (201 for create,...
artifact: guidelines/networking/api-design.md
version: 1.0.0
---

## Worker Focus
Client calls match REST conventions — correct HTTP methods, no verb-in-URL, proper status code handling (201 for create, 204 for delete, 422 for validation); URL path versioning respected

## Verify
Client uses GET for reads, POST for creates, DELETE for removes; 201 responses extract Location header; 422 responses display field-level errors; client handles versioned URL paths
