---
name: search-integration-windows
description: Use Windows Search indexer with `ISearchManager` and property handlers; register file type associations and protocol han...
artifact: guidelines/platform/search-integration.md
version: 1.0.0
---

## Worker Focus
Use Windows Search indexer with `ISearchManager` and property handlers; register file type associations and protocol handlers so content appears in Start menu search; for WinUI, use in-app search with system integration via `SearchPane` or equivalent; keep index current; each indexed item deep links back to content

## Verify
File type associations registered in manifest; property handlers deployed for custom file types; indexed items resolve via protocol activation; search results navigate to correct content
