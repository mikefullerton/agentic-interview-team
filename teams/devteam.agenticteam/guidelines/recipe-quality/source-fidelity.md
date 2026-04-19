---

id: 47563e88-307b-4eef-a63c-ddc18e85a945
title: "Source Fidelity"
domain: agentic-cookbook://guidelines/cookbook/recipe-quality/source-fidelity
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Recipe accurately captures what the source code does without invention, idealization, or omission of documented quirks."
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

# Source Fidelity

A recipe extracted from existing code serves as a faithful specification of that code's actual behavior — not an idealized description of what the code should do, not a projection of best practices onto what it happens to do, and not a sanitized narrative that hides its rough edges. Source fidelity is the quality dimension that holds a recipe accountable to the source of truth: the running code. When a recipe fails source fidelity, implementations built from it will diverge from the reference behavior, and teams will lose the trust that makes the cookbook useful.

## Requirements

### Traceability

- Every behavioral requirement in the recipe MUST be traceable to a specific, observable behavior in the source code. Traceability means a reviewer can point to the code path, API response, or test case that demonstrates the behavior.
- Requirements MUST NOT be invented to fill perceived gaps. If the source code does not implement a behavior, the recipe MUST NOT require it.
- Where traceability is indirect (e.g., behavior is inferred from a test rather than inspected in production code), the recipe SHOULD note the evidence source in a comment or Design Decisions entry.
- Requirements that are partially observable — where some aspect of the behavior cannot be confirmed from the code alone — MUST be marked `NEEDS REVIEW` with an explanation of what cannot be confirmed and why.

### Accurate Representation of Gaps

- If the source code does not implement support for a concern (e.g., accessibility, internationalization, offline handling), the recipe MUST NOT fabricate requirements for that concern.
- Unimplemented sections MUST be marked with `NEEDS REVIEW: Not implemented in source. Behavior undefined.` This signals to consumers that the recipe is incomplete in a specific way, rather than silently omitting the concern.
- A recipe MUST NOT mark a section `NEEDS REVIEW` when the behavior is actually implemented and observable. `NEEDS REVIEW` is reserved for genuine gaps in the source, not for sections the author found tedious to analyze.

### Honest Representation of Quirks and Workarounds

- If the source code contains a known workaround, a platform-specific hack, or behavior that deviates from what a naive reader would expect, the recipe MUST document it. These deviations MUST appear in a Design Decisions section or as inline notes on the affected requirements.
- The recipe MUST NOT smooth over quirks by describing the idealized behavior and omitting the actual behavior.
- If the source code handles a case in an unusual or non-obvious way (e.g., a retry loop that silently drops errors after three attempts), the recipe MUST document that behavior as a requirement or a noted deviation, not omit it.
- Technical debt in the source SHOULD be noted in Design Decisions when it affects behavioral correctness. Authors MUST NOT treat documentation of technical debt as optional when the debt affects how implementations must behave.

### Error Handling Accuracy

- If the source code silently swallows exceptions, ignores error return codes, or fails to communicate errors to the caller or user, the recipe MUST accurately document this — not describe the error handling the code should have had.
- A recipe that claims `MUST display an error message on failure` when the source code makes no such attempt is a source fidelity failure regardless of whether the behavior is desirable.

### No Idealization

- The recipe MUST describe the code as it is, not as the author believes it should be. Aspirational behavior belongs in a separate "Recommended Improvements" section if included at all, and MUST be clearly distinguished from normative requirements.
- Requirements derived from what "a well-implemented component would do" rather than what the code actually does are a source fidelity violation.

## Common Violations

- **Invented accessibility requirements.** The source code contains no VoiceOver or ARIA support. The recipe's Accessibility section includes five MUST requirements for screen reader behavior. These requirements are invented; no implementation can verify them against the source.
- **Omitting a documented workaround.** The source code patches a race condition by debouncing a search field with a 400ms delay. The recipe describes the search behavior without mentioning the debounce, causing implementors on other platforms to miss the timing requirement.
- **Idealizing error handling.** The source code catches a network error and logs it to the console, providing no user-facing feedback. The recipe states: `MUST display a retry prompt when the network request fails.` This is the desired behavior, not the actual behavior.
- **Claiming silent failures don't exist.** A data write function calls a database write operation without checking the return value or catching exceptions. The recipe states the component `MUST persist data reliably`. The source provides no such guarantee.
- **NEEDS REVIEW hiding laziness, not gaps.** Every section of the Accessibility review is marked `NEEDS REVIEW` even though the source code has extensive VoiceOver labels. The marker is used to avoid analysis, not to flag genuine gaps.
- **Aspirational requirements presented as normative.** The source truncates long strings with an ellipsis. The recipe states: `MUST truncate with an ellipsis and provide a tooltip with the full text.` The tooltip is not implemented; the author added it because it seemed like good practice.

## Verification Checklist

A verifier MUST check each of the following items. The recipe PASSES source fidelity only if every item is satisfied.

- [ ] Every normative requirement can be traced to observable source code behavior or a cited test case.
- [ ] No requirement describes behavior that does not exist in the source code.
- [ ] All known workarounds, hacks, or non-obvious behavioral patterns in the source are documented in Design Decisions or as inline notes.
- [ ] Sections covering concerns not implemented in the source are marked `NEEDS REVIEW: Not implemented in source` rather than containing invented requirements.
- [ ] `NEEDS REVIEW` markers are used only for genuine gaps — not as a substitute for analysis.
- [ ] Error handling requirements accurately reflect what the code does on failure, not what it should do.
- [ ] No aspirational or "best practice" behavior is presented as a normative MUST requirement without being traceable to the source.
- [ ] Technical debt affecting behavioral correctness is documented in Design Decisions.
- [ ] Any "Recommended Improvements" content is clearly separated from normative requirements and is not written using RFC keywords.

## Change History
