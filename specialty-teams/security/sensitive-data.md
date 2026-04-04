---
name: sensitive-data
description: Data minimization with explicit DTOs (not raw DB models), PII classification tiers, field-level encryption for SSN/payme...
artifact: guidelines/security/sensitive-data.md
version: 1.0.0
---

## Worker Focus
Data minimization with explicit DTOs (not raw DB models), PII classification tiers, field-level encryption for SSN/payment via KMS, no PII/tokens/passwords in logs at any level

## Verify
API responses use explicit DTOs; highly sensitive fields encrypted at app layer; no PII or token values in log output; KMS used for SSN/payment
