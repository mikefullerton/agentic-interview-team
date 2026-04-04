---
name: reliability-compliance
description: 8 compliance checks — error-recovery, graceful-degradation, fault-tolerance, state-recovery, idempotent-operations, time...
artifact: compliance/reliability.md
version: 1.0.0
---

## Worker Focus
8 compliance checks — error-recovery, graceful-degradation, fault-tolerance, state-recovery, idempotent-operations, timeout-handling, data-integrity, health-observability

## Verify
Each compliance check has a status (passed/failed/partial/n-a) with evidence; transient errors retried without user intervention; external dependency failure degrades gracefully (no crash); timed-out operations leave system in consistent state; persistent components emit health metrics
