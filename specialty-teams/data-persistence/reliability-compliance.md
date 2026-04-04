---
name: reliability-compliance
description: 8 compliance checks — error-recovery, graceful-degradation, fault-tolerance, state-recovery, idempotent-operations, time...
artifact: compliance/reliability.md
version: 1.0.0
---

## Worker Focus
8 compliance checks — error-recovery, graceful-degradation, fault-tolerance, state-recovery, idempotent-operations, timeout-handling, data-integrity, health-observability

## Verify
Each compliance check has a status (passed/failed/partial/n-a) with evidence; state restored correctly after process restart; write operations that may be retried are idempotent; data integrity validated on read and write with corrupt data detected and reported
