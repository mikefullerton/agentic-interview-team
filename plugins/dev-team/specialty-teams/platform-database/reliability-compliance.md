---
name: reliability-compliance
description: 8 compliance checks — error-recovery (transient error handling with retry), graceful-degradation (unavailable dependency...
artifact: compliance/reliability.md
version: 1.0.0
---

## Worker Focus
8 compliance checks — error-recovery (transient error handling with retry), graceful-degradation (unavailable dependency fallback), fault-tolerance (no crashes on unexpected input), state-recovery (persistent state survives restart), idempotent-operations (safe retries), timeout-handling (consistent state after timeout), data-integrity (corrupt data detected and reported), health-observability (long-running services emit health metrics)

## Verify
Each compliance check has a status (passed/failed/partial/n-a) with evidence; retry logic present for network/IO calls; no operations that wait indefinitely without a timeout; state can be restored after process kill and restart
