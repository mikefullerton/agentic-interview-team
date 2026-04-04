---
name: search-integration
description: Use Firebase App Indexing or `AppIndexingApi` for on-device search integration; declare searchable content in `searchabl...
artifact: guidelines/platform/search-integration.md
version: 1.0.0
---

## Worker Focus
Use Firebase App Indexing or `AppIndexingApi` for on-device search integration; declare searchable content in `searchable.xml` and implement `SearchableInfo`; support Google Assistant via structured content markup; keep index current; each indexed item deep links back to content

## Verify
`searchable.xml` present and registered in manifest; `SearchableInfo` implemented; indexed items deep link correctly; stale entries removed when content deleted
