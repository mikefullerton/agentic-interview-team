---

id: 4428deb0-05a8-4b52-a78f-3dec1e7f90a4
title: "MSIX Packaging"
domain: agentic-cookbook://guidelines/shipping/msix-packaging
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "- Use the single-project MSIX packaging model"
platforms: 
  - windows
tags: 
  - msix-packaging
  - platform
  - windows
depends-on: []
related: []
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - platform-integration
  - pre-pr
---

# MSIX Packaging

Package Windows apps with the single-project MSIX model, declare minimal capabilities, and sign with a trusted certificate.

- Use the single-project MSIX packaging model
- Capabilities MUST be declared minimally in `Package.appxmanifest`
- Packages MUST be signed with a trusted certificate for sideloading
- Version numbering MUST use `Major.Minor.Build.Revision`, monotonically increasing

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
