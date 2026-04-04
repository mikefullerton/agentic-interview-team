---
name: python-use-roadmaplib
description: Use `roadmap_lib` functions for all roadmap operations (reading state, parsing frontmatter, finding steps); never reimpl...
artifact: guidelines/language/python/use-roadmaplib.md
version: 1.0.0
---

## Worker Focus
Use `roadmap_lib` functions for all roadmap operations (reading state, parsing frontmatter, finding steps); never reimplement what already exists in the library

## Verify
No duplicate implementations of frontmatter parsing, state reading, or step finding; `roadmap_lib` imported and used for roadmap operations
