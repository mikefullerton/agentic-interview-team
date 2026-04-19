---

id: d65ed7a3-6125-4c9f-b3af-f3b26ad61dfb
title: "Completeness"
domain: agentic-cookbook://guidelines/cookbook/recipe-quality/completeness
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "No section is empty without explanation, all gaps are tracked with NEEDS REVIEW, and edge cases and test vectors provide comprehensive coverage."
platforms:
  - csharp
  - ios
  - kotlin
  - typescript
  - web
  - windows
tags:
  - recipe-quality
depends-on: []
related: []
references: []
triggers:
  - recipe-authoring
---

# Completeness

Completeness measures whether a recipe provides enough information for an implementor to build a conformant component and for a verifier to assess that conformance — without gaps that require guesswork. A recipe can satisfy template conformance (all sections present) and source fidelity (nothing invented) while still being incomplete: sections with placeholder content, edge cases left unaddressed, or test vectors that cover only the happy path. This guideline defines what "complete" means for each part of a recipe.

## Requirements

### Section Content

- Every required section MUST contain meaningful content. A section with only a heading and no body content is NOT permitted.
- If a section cannot be filled because the information is unavailable or the concern is not yet analyzed, the section MUST be marked with `NEEDS REVIEW` followed by an explanation that:
  1. States specifically what information is missing (not just "to be completed").
  2. Explains why it could not be determined during recipe creation.
  3. Identifies who or what could resolve the gap (e.g., "requires review of accessibility audit results" or "pending confirmation from the iOS team").
- `NEEDS REVIEW` markers MUST NOT be stacked — multiple gaps in one section MUST each have their own labeled marker explaining the specific gap.
- A `NEEDS REVIEW` marker MUST NOT be used as a placeholder for content the author intends to add later. It is a formal gap declaration, not a reminder note.

### Edge Cases Coverage

- The Edge Cases section MUST address each of the following categories that are applicable to the recipe's domain:
  - **Null and empty input**: What happens when required inputs are null, empty string, zero, or an empty collection?
  - **Boundary values**: What happens at the minimum and maximum valid values for any constrained input?
  - **Concurrent access**: If the component can be accessed or mutated from multiple threads or sessions simultaneously, what is the defined behavior?
  - **Error states**: What happens when a dependency (network, database, file system) is unavailable or returns an error?
  - **Offline or disconnected state**: If the component operates over a network, what happens when connectivity is lost mid-operation?
- If a category is not applicable to the recipe's domain, the recipe MUST include a brief statement explaining why (e.g., "Concurrent access: this component is single-threaded and access is serialized by the main queue.").
- Edge cases MUST NOT be limited to the happy path and one error case. The Edge Cases section MUST reflect deliberate analysis of failure modes, not a minimal token response.
- Each edge case entry MUST state the input or condition, the expected behavior, and whether the behavior is a MUST or SHOULD.

### Conformance Test Vectors

- The Conformance Test Vectors section MUST include at least one test vector for every MUST requirement in the Behavioral Requirements section. No MUST requirement MAY be left without a corresponding test vector.
- Each test vector MUST specify: the precondition or input, the action taken, and the expected observable outcome. Outcome descriptions MUST be concrete enough that two independent testers reach the same PASS/FAIL conclusion.
- Test vectors MUST NOT be limited to happy-path scenarios. Each MUST requirement that involves a failure mode MUST have a test vector that exercises that failure.
- SHOULD requirements SHOULD have test vectors. When SHOULD requirements do not have test vectors, the omission MUST be documented with a rationale.
- Test vectors MUST be numbered or labeled so that individual vectors can be referenced in bug reports and review comments.

### Design Decisions

- If the recipe's Behavioral Requirements section contains any non-obvious constraint — one that a competent developer reading the code would not immediately understand the rationale for — the Design Decisions section MUST explain it.
- The Design Decisions section MUST NOT be empty if any SHOULD requirement exists, because every SHOULD implies a permissible deviation and the rationale for the default MUST be explained.

## Common Violations

- **Empty section with no explanation.** The Accessibility section contains only the heading `## Accessibility` and a single line: "See platform guidelines." The content is not meaningful, and no `NEEDS REVIEW` marker explains what is missing or why.
- **NEEDS REVIEW with no context.** `## States\n\nNEEDS REVIEW` — The marker provides no information about what states are unknown, why they couldn't be determined, or who can resolve the gap. A reviewer reading this cannot act on it.
- **Missing concurrent access edge case.** A recipe for a shared cache component addresses null inputs and boundary values but says nothing about concurrent reads and writes. Concurrent access is directly applicable and its omission is a completeness failure.
- **Test vectors that only cover the happy path.** The Conformance Test Vectors section has eight test vectors, all of which test successful completion. The recipe has four MUST requirements involving error states, none of which have a corresponding test vector.
- **Test vector too vague to produce a PASS/FAIL.** "Test that the button handles errors gracefully." No precondition, no specific action, no measurable outcome. Two testers will reach different conclusions.
- **NEEDS REVIEW as a reminder.** `NEEDS REVIEW: Need to check with design on the hover state colors.` This is a work-in-progress note, not a formal gap declaration. A recipe in this state MUST NOT be submitted for review.
- **No rationale for non-obvious SHOULD.** A requirement states `SHOULD debounce search input by at least 300ms.` The Design Decisions section is empty. The 300ms threshold and the debounce requirement are non-obvious; developers who deviate cannot know whether they are violating a performance constraint or a UX preference.

## Verification Checklist

A verifier MUST check each of the following items. The recipe PASSES completeness only if every item is satisfied.

- [ ] Every required section contains meaningful body content or a properly formatted `NEEDS REVIEW` marker.
- [ ] Every `NEEDS REVIEW` marker identifies what is missing, why it couldn't be determined, and who can resolve it.
- [ ] No section uses `NEEDS REVIEW` as a placeholder for future authoring.
- [ ] The Edge Cases section addresses null/empty input, boundary values, concurrent access (or explains inapplicability), error states, and offline/disconnected state (or explains inapplicability).
- [ ] Each edge case entry states the condition, the expected behavior, and its normative level (MUST/SHOULD).
- [ ] Every MUST requirement in Behavioral Requirements has at least one corresponding numbered test vector.
- [ ] Every test vector specifies a precondition, an action, and a concrete measurable expected outcome.
- [ ] Test vectors cover failure modes, not only the happy path.
- [ ] SHOULD requirements without test vectors have documented rationale for the omission.
- [ ] The Design Decisions section explains any non-obvious MUST constraint.
- [ ] The Design Decisions section is non-empty if any SHOULD requirement exists.

## Change History
