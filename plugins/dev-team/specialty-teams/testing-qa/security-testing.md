---
name: security-testing
description: Run SAST (Semgrep all languages, Bandit for Python, CodeQL for deep analysis), dependency scanning (pip-audit, npm audit...
artifact: guidelines/testing/security-testing.md
version: 1.0.0
---

## Worker Focus
Run SAST (Semgrep all languages, Bandit for Python, CodeQL for deep analysis), dependency scanning (pip-audit, npm audit, dotnet vulnerable, Snyk), and DAST (OWASP ZAP for running web services) as part of post-generation verification

## Verify
`semgrep scan --config=auto .` run with no critical findings; dependency audit command run with no high/critical vulnerabilities; OWASP ZAP scan run against local service if web-facing
