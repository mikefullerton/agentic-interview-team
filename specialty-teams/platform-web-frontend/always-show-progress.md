---
name: always-show-progress
description: Implement determinate progress bars (with percentage) and indeterminate spinners/skeletons/shimmer in the DOM; prevent U...
artifact: guidelines/ui/always-show-progress.md
version: 1.0.0
---

## Worker Focus
Implement determinate progress bars (with percentage) and indeterminate spinners/skeletons/shimmer in the DOM; prevent UI freeze during async operations

## Verify
No async operation leaves the DOM visually frozen; skeleton/shimmer uses CSS animations; progress bar updates as work completes
