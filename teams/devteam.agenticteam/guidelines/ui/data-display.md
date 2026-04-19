---

id: 704fef7e-0e8d-480c-8019-cf84b5fd851b
title: "Data Display"
domain: agentic-cookbook://guidelines/implementing/ui/data-display
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-03-27
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Choose the right pattern for the content type and user task."
platforms: []
tags: 
  - data-display
  - ui
depends-on: []
related: []
references: 
  - https://developer.apple.com/design/human-interface-guidelines/lists-and-tables
  - https://m3.material.io/components/lists/overview
  - https://www.nngroup.com/articles/cards-component/
approved-by: "approve-artifact v1.0.0"
approved-date: "2026-04-04"
triggers:
  - ui-implementation
  - data-modeling
---

# Data Display

Choose the right pattern for the content type and user task.

- **List** — sequential, scannable content. Best for homogeneous items where the user reads
  top-to-bottom (messages, settings, search results). Support pull-to-refresh and pagination
  for dynamic data.
- **Table** — comparable, multi-attribute data. Best for desktop/tablet when users need to
  compare values across rows (spreadsheets, admin panels, logs). Tables MUST be sortable
  by column. On mobile, consider collapsing to cards or a detail-on-tap list.
- **Cards** — heterogeneous, browsable content. Best when items have varying content types
  or sizes (news feed, dashboard widgets). Cards should each be a single tappable unit with
  one primary action.
- **Grid** — uniform visual items. Best for content where the visual is primary (photos,
  products, icons). Maintain consistent aspect ratios.

Collections of **10+ items** SHOULD provide sort and/or filter controls. Collections of **50+ items**
MUST include search.

References:
- [Apple HIG: Lists and Tables](https://developer.apple.com/design/human-interface-guidelines/lists-and-tables)
- [Material Design: Lists](https://m3.material.io/components/lists/overview)
- [NNGroup: Cards](https://www.nngroup.com/articles/cards-component/)

## Change History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0.2 | 2026-04-09 | Mike Fullerton | Add trigger tags |
| 1.0.1 | 2026-04-09 | Mike Fullerton | Reorganize into use-case directory |
| 1.0.0 | 2026-03-27 | Mike Fullerton | Initial creation |
