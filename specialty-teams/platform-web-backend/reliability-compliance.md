---
name: reliability-compliance
description: 8 compliance checks — error-recovery (retry transient failures), graceful-degradation (handle unavailable dependencies),...
artifact: compliance/reliability.md
version: 1.0.0
---

## Worker Focus
8 compliance checks — error-recovery (retry transient failures), graceful-degradation (handle unavailable dependencies), fault-tolerance (no crash on unexpected input), state-recovery (restore after restart), idempotent-operations, timeout-handling (consistent state after timeout), data-integrity, health-observability

## Verify
Each check has status (passed/failed/partial/n-a) with evidence; timeout handling leaves no dangling locks or partial writes; idempotent endpoints verified as safe to retry
