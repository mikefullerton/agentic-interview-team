---
id: 8A9E6D0E-CC26-497C-867B-3171A0213F5A
title: "Privacy and Data"
domain: agentic-cookbook://compliance/privacy-and-data
type: compliance
version: 1.0.0
status: draft
language: en
created: 2026-03-28
modified: 2026-03-28
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Compliance checks for data privacy, personal data handling, and secure storage."
platforms: []
tags: [compliance, privacy, data]
depends-on: []
related:
  - agentic-cookbook://compliance/security
  - agentic-cookbook://compliance/platform-compliance
  - agentic-cookbook://compliance/user-safety
references: []
---

# Privacy and Data

Compliance checks that govern how components collect, store, transmit, and process personal and sensitive data. These checks ensure respect for user privacy, compliance with data protection principles, and responsible data stewardship.

## Applicability

Any recipe or guideline that collects, stores, transmits, or processes personal or sensitive data.

## Checks

### data-minimization

Components MUST collect only the minimum data necessary for their functionality.

**Applies when:** a component requests, collects, or stores user data.

**Guidelines:**
- [Privacy](agentic-cookbook://guidelines/security/privacy)

---

### consent-before-collection

Personal data collection MUST be preceded by informed user consent.

**Applies when:** a component collects personal or identifiable information from the user.

**Guidelines:**
- [Privacy](agentic-cookbook://guidelines/security/privacy)

---

### secure-data-storage

Personal and sensitive data MUST be stored using platform-specific secure storage.

**Applies when:** a component persists personal or sensitive data locally or remotely.

**Guidelines:**
- [Secure Storage](agentic-cookbook://guidelines/security/secure-storage)
- [Sensitive Data](agentic-cookbook://guidelines/security/sensitive-data)

---

### no-pii-in-logs

Personally identifiable information MUST NOT appear in log output at any level.

**Applies when:** a component writes log output and has access to personal data.

**Guidelines:**
- [Sensitive Data](agentic-cookbook://guidelines/security/sensitive-data)
- [Logging](agentic-cookbook://guidelines/observability/logging)

---

### data-retention-policy

Components handling personal data MUST define retention duration and deletion behavior.

**Applies when:** a component stores personal data beyond the current session.

**Guidelines:**
- [Privacy](agentic-cookbook://guidelines/security/privacy)

---

### data-portability

Users SHOULD be able to export their personal data in a standard format.

**Applies when:** a component stores significant amounts of user-generated or personal data.

**Guidelines:**
- [Privacy](agentic-cookbook://guidelines/security/privacy)

---

### third-party-disclosure

Data sharing with third parties MUST be disclosed and require user consent.

**Applies when:** a component transmits user data to external services or analytics providers.

**Guidelines:**
- [Privacy](agentic-cookbook://guidelines/security/privacy)

---

### encryption-at-rest

Sensitive data stored locally MUST be encrypted at rest.

**Applies when:** a component persists sensitive data to the local filesystem or database.

**Guidelines:**
- [Sensitive Data](agentic-cookbook://guidelines/security/sensitive-data)
- [Secure Storage](agentic-cookbook://guidelines/security/secure-storage)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-28 | Mike Fullerton | Initial creation |
