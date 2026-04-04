---
name: logging
description: Every component and flow instrumented with structured logging using platform best-in-class framework (os.log/Logger on A...
artifact: guidelines/logging/logging.md
version: 1.0.0
---

## Worker Focus
Every component and flow instrumented with structured logging using platform best-in-class framework (os.log/Logger on Apple, Timber on Android, console/pino/winston on web, logging module on Python, ILogger<T> on .NET); debug level for flow instrumentation; log state transitions, user interactions, async start/completion/failure; never log PII at any level

## Verify
Every component has a logger instance; structured logging framework used (not raw print/console.log/NSLog); no PII in log output; async task lifecycle (start/complete/fail) logged; C# uses message templates not string interpolation
