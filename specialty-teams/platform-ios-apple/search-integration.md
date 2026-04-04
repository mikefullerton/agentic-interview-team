---
name: search-integration
description: Use Core Spotlight (`CSSearchableItem`, `CSSearchableItemAttributeSet`) to index content; on iOS 17+ use `IndexedEntity`...
artifact: guidelines/platform/search-integration.md
version: 1.0.0
---

## Worker Focus
Use Core Spotlight (`CSSearchableItem`, `CSSearchableItemAttributeSet`) to index content; on iOS 17+ use `IndexedEntity` for semantic indexing; donate `NSUserActivity` for Handoff-eligible items to appear in Spotlight suggestions; keep index current (add on create, remove on delete); each indexed item must deep link back to content

## Verify
`CSSearchableItemAttributeSet` populated with title, description, thumbnail; indexed items deep link correctly; stale items removed when content deleted; `NSUserActivity` donated for key screens
