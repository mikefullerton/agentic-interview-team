---
name: optimize-for-change
description: Every architectural decision evaluated by whether it makes future change easier or harder; all other principles (composi...
artifact: principles/meta-principle-optimize-for-change.md
version: 1.0.0
---

## Worker Focus
Every architectural decision evaluated by whether it makes future change easier or harder; all other principles (composition, DI, boundaries, SoC) are strategies for reducing change cost; use this as the meta-question when tradeoffs arise

## Verify
Architectural decisions can be articulated in terms of change cost; no "easier now, harder later" shortcuts taken without explicit acknowledgment; key extension points (swappable backends, injectable services) present where change is anticipated
