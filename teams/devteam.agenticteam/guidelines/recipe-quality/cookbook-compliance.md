---

id: 0d3aaa29-0ce3-4803-8f8a-a7023713b574
title: "Cookbook Compliance"
domain: agentic-cookbook://guidelines/cookbook/recipe-quality/cookbook-compliance
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Recipe aligns with applicable cookbook guidelines and does not contradict platform-wide principles for security, accessibility, and error handling."
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

# Cookbook Compliance

A recipe does not exist in isolation. The cookbook defines platform-wide guidelines that establish floors — minimum standards every recipe must meet or exceed for security, accessibility, error handling, and other cross-cutting concerns. Cookbook compliance verifies that a recipe's behavioral requirements are consistent with those guidelines, references them where applicable, and does not silently contradict them. A recipe that passes template conformance and behavioral quality but contradicts a security guideline is still a defective artifact.

## Requirements

### Non-Contradiction

- A recipe's behavioral requirements MUST NOT contradict any applicable cookbook guideline.
- Where a cookbook guideline establishes a MUST, the recipe's requirements MUST be at least as strict. A recipe MUST NOT relax a cross-cutting MUST to a SHOULD or MAY without an explicit documented exception approved by the cookbook maintainers.
- Where a recipe's domain intersects with multiple guidelines, all applicable guidelines MUST be satisfied simultaneously. Compliance with one guideline MUST NOT be used to justify non-compliance with another.

### Referencing Applicable Guidelines

- When a cookbook guideline directly applies to the recipe's domain, the recipe SHOULD cite the guideline in the `depends-on` or `references` frontmatter field.
- When a requirement in the recipe is derived from or constrained by a guideline, the requirement SHOULD include an inline reference (e.g., `per agentic-cookbook://guidelines/accessibility/touch-targets`).
- Authors MUST NOT silently incorporate guideline content without attribution. Duplicating guideline text verbatim into a recipe without reference creates maintenance drift when the guideline changes.

### Security-Relevant Recipes

- Any recipe whose subject matter involves authentication, authorization, session management, token handling, credential storage, or transmission of sensitive data MUST include a dedicated section or sub-section addressing the relevant security concerns.
- Security requirements MUST address at minimum: what data is considered sensitive in this context, how that data MUST be stored or transmitted, and what MUST happen when a security violation is detected.
- A security-relevant recipe MUST NOT leave token lifetimes, storage mechanisms, or revocation behavior unspecified.
- Security requirements MUST NOT defer entirely to "follow platform best practices" without citing specific practices.

### UI and Accessibility

- Any recipe whose subject matter involves a visible user interface element or user interaction flow MUST address accessibility.
- UI recipes MUST include requirements covering: keyboard and assistive technology navigation, minimum contrast ratios, touch/click target sizes, and meaningful labels for interactive controls.
- UI recipes MUST NOT treat accessibility as optional (MAY) when the relevant platform requires it by law or platform policy (e.g., WCAG 2.1 AA for web, Apple Human Interface Guidelines for iOS).
- UI recipes SHOULD reference the applicable accessibility guideline in the `depends-on` field.

### Networking and Error Handling

- Any recipe whose subject matter involves network requests, API calls, or external service communication MUST include requirements for: failure modes (timeout, unreachable host, unexpected status codes), retry behavior (including backoff strategy), and user-facing error communication.
- Networking recipes MUST NOT treat error handling as a SHOULD when failure is a routine operating condition (e.g., mobile networking).

### Data Persistence

- Any recipe that writes to local storage, a database, or a file system MUST specify durability guarantees: what data survives an app restart, what is ephemeral, and under what conditions data may be lost.
- Recipes that handle user-generated content MUST specify whether and how data is backed up and how conflicts are resolved.

## Common Violations

- **Security recipe ignoring token handling.** A recipe for an OAuth login flow specifies the redirect URI and scope parameters but never addresses where the access token is stored, how long it lives, or what happens when it expires. The recipe appears complete but omits the most security-critical decisions.
- **UI recipe with no accessibility section.** A recipe for a custom modal dialog defines visual appearance and animation transitions but contains no requirements for focus management, `aria` roles, or keyboard dismissal. The recipe is unusable for accessible implementations.
- **Networking recipe with no error handling.** A recipe for a data-fetching pattern specifies only the happy path — successful response parsing — with no mention of timeouts, HTTP errors, or retry limits. Implementations built from this recipe will fail ungracefully in production.
- **Contradicting a guideline.** A guideline requires all form submissions to display a confirmation message. A recipe for a delete-account flow specifies that the action is immediate and irreversible on tap, with no confirmation step. The recipe silently contradicts the guideline.
- **Guideline content duplicated without reference.** A recipe copy-pastes three paragraphs from an accessibility guideline verbatim. When the guideline is updated, the recipe is now stale and provides incorrect information with no indication that it has diverged.
- **Blanket "follow best practices" placeholder.** A security section reads: "MUST follow platform security best practices for credential storage." This is unverifiable and untestable. A verifier cannot determine which practices apply or whether the implementation complied.

## Verification Checklist

A verifier MUST check each of the following items. The recipe PASSES cookbook compliance only if every item is satisfied.

- [ ] No behavioral requirement in the recipe contradicts a MUST in any applicable cookbook guideline.
- [ ] Where cookbook guidelines apply to this recipe's domain, they are cited in `depends-on` or `references`.
- [ ] If the recipe involves authentication, authorization, or sensitive data: a security section is present covering storage, transmission, and violation handling.
- [ ] If the recipe involves authentication, authorization, or sensitive data: token lifetimes, storage mechanisms, and revocation are specified.
- [ ] If the recipe involves a UI element or interaction: an accessibility section is present.
- [ ] If the recipe involves a UI element: requirements cover contrast, touch target size, keyboard navigation, and control labels.
- [ ] If the recipe involves network requests: failure modes, retry behavior, and user-facing error communication are all addressed.
- [ ] If the recipe involves data persistence: durability guarantees and backup/conflict behavior are specified.
- [ ] No requirement defers entirely to "best practices" without citing specific, verifiable practices.
- [ ] No guideline content is reproduced verbatim without a reference back to the source guideline.

## Change History
