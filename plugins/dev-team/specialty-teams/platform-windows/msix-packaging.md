---
name: msix-packaging
description: Use single-project MSIX packaging model; declare capabilities minimally in `Package.appxmanifest`; sign packages with a ...
artifact: guidelines/platform/windows/msix-packaging.md
version: 1.0.0
---

## Worker Focus
Use single-project MSIX packaging model; declare capabilities minimally in `Package.appxmanifest`; sign packages with a trusted certificate for sideloading; version numbering follows `Major.Minor.Build.Revision` monotonically increasing scheme

## Verify
Single-project packaging model used; only required capabilities declared in manifest; package signed with certificate; version number monotonically increases across releases
