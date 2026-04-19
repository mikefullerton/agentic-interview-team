---

id: b512282a-8174-426f-95dd-4a147222584d
title: "Search integration"
domain: agentic-cookbook://guidelines/implementing/platform-integration/search-integration
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-02
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "App content SHOULD be discoverable through the platform's system search, enabling users to find content without opening the app."
platforms: 
  - ios
  - macos
  - android
  - windows
  - web
tags: 
  - search
  - platform
  - discoverability
depends-on:
  - agentic-cookbook://principles/support-automation
related:
  - agentic-cookbook://guidelines/platform/deep-linking
references: []
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - platform-integration
---

# Search integration

App content SHOULD be discoverable through the platform's system search, enabling users to find content without opening the app. Search integration turns the app from an island into a participant in the user's information flow.

- Index content that users would reasonably search for — documents, contacts, messages, settings
- Keep the search index current — add items when created, remove when deleted
- Each indexed item MUST deep link back to the relevant content
- Include rich metadata (thumbnails, descriptions, categories) for meaningful search results

## Apple (iOS / macOS)

Use Core Spotlight (`CSSearchableItem`, `CSSearchableItemAttributeSet`) to index content. On iOS 17+, conform entities to `IndexedEntity` for semantic indexing with natural language support. Support `NSUserActivity` donation for Handoff-eligible items to appear in Spotlight suggestions.

## Android

Use Firebase App Indexing or `AppIndexingApi` for on-device search integration. Declare searchable content in `searchable.xml` and implement `SearchableInfo`. Support Google Assistant via structured content markup.

## Windows

Use the Windows Search indexer with `ISearchManager` and property handlers. Register file type associations and protocol handlers so content appears in Start menu search. For UWP/WinUI, use `SearchPane` or in-app search with system integration.

## Web

Use structured data (JSON-LD, Schema.org) for search engine discoverability. Implement OpenGraph and Twitter Card meta tags. Support the Web App Manifest for PWA search integration. Ensure server-side rendering or pre-rendering for crawlability.

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-04-02 | Mike Fullerton | Initial creation |
