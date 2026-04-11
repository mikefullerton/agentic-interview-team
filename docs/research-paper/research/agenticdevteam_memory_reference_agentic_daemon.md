---
name: agentic-daemon project reference
description: User's existing macOS launchd-based job-runner daemon. Target phase-2 host for conductor sessions.
type: reference
originSessionId: 1529e1c6-c334-497e-83d0-d341413f38f4
---
Project at `~/projects/active/agentic-daemon`. A macOS user-space daemon (Swift) managed by launchd that watches a jobs directory, compiles Swift scripts, and runs them on configurable schedules. Installed via `./install.sh`; stdout/stderr go to `~/Library/Logs/com.agentic-cookbook.daemon/` and macOS unified logging.

**Relevance to dev-team:** Designated phase-2 host for conductor sessions (see project_conductor_pivot). Needs these additions before it can host conductors:
- Non-Swift job types (Python service jobs).
- Service-mode jobs that run until session completion, not on a schedule.
- A structured client-attach contract (unix socket candidate) so out-of-process clients can connect to a running job.

**When to apply:** If the user asks about where conductor sessions should run, or about extending the daemon, or about cross-machine/background-run concerns — this project is the target host and starting point.
