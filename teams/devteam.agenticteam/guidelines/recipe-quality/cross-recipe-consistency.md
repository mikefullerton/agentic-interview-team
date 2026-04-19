---

id: 19648d85-adba-4f38-b513-a38ca58e9fb0
title: "Cross-Recipe Consistency"
domain: agentic-cookbook://guidelines/cookbook/recipe-quality/cross-recipe-consistency
type: guideline
version: 1.0.2
status: accepted
language: en
created: 2026-04-07
modified: 2026-04-09
author: Mike Fullerton
copyright: 2026 Mike Fullerton
license: MIT
summary: "Naming, structure, and depth are consistent across sibling recipes so the cookbook reads as a coherent whole."
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

# Cross-Recipe Consistency

A cookbook is not a collection of isolated documents — it is a system. Recipes within the same component tree, domain, or category form a family of sibling artifacts that teams navigate together. When sibling recipes use inconsistent terminology, wildly different levels of detail, or incompatible tagging conventions, the cookbook loses coherence: consumers cannot form reliable mental models, cross-references break, and automated tooling produces unreliable results. Cross-recipe consistency holds a recipe accountable not just to its own quality, but to the quality of the family it belongs to.

## Requirements

### Terminology

- Sibling recipes (recipes that share the same parent node in the cookbook component tree) MUST use consistent terminology for shared concepts. If one recipe calls the authenticated user a "user", all siblings MUST do the same. Introducing "account", "member", "principal", or "identity" for the same concept in a sibling recipe is a consistency violation.
- When a term is established in an earlier recipe in a family, subsequent sibling recipes MUST adopt it without modification. Authors MUST NOT introduce synonyms for existing terms.
- Where terminology is defined in a cookbook-level glossary or guideline, recipes MUST use the canonical term. Deviating from canonical terminology requires an explicit note in Design Decisions explaining why the deviation is justified.
- Concepts that differ between siblings (e.g., "guest user" vs. "authenticated user") MUST be distinguished using distinct, consistent names — not context-dependent uses of the same word.

### Structural Depth and Detail

- Sibling recipes of comparable complexity SHOULD have comparable section depth. A recipe with 3 behavioral requirements and a sibling of similar functional complexity with 20 behavioral requirements is a consistency signal that one or both recipes are incorrectly scoped.
- "Comparable complexity" is defined by the number of distinct behaviors the component supports, the number of states it can occupy, and the number of error conditions it must handle — not by its visual simplicity.
- When a depth disparity between siblings exists, it MUST be explained. Either the simpler recipe is incomplete (a completeness failure), or the more detailed recipe is over-specified (an authoring quality issue), or the complexity difference is genuinely warranted and SHOULD be noted in Design Decisions.
- No recipe in a sibling group MAY set a depth standard so far above or below the others that it makes the group incoherent to a first-time reader.

### Frontmatter Conventions

- All recipes in a family MUST use the same tag vocabulary. If one recipe in a family uses the tag `form-validation`, all siblings addressing the same concept MUST use `form-validation` — not `validation`, `input-validation`, or `forms`.
- Platform identifiers in the `platforms` field MUST use the cookbook's canonical platform names. A recipe MUST NOT list `iOS` when siblings list `ios`, or `TypeScript` when siblings list `typescript`.
- The `author` field format MUST be consistent across a family (e.g., if siblings use `Given Family`, a new recipe MUST not use `family, given` or an email address).
- `version` fields across a sibling family are independent — each recipe is versioned individually — but the starting version for new recipes MUST be consistent (all start at `1.0.0` or all start at `0.1.0`, as established by the family convention).

### Cross-References

- When a recipe references a sibling recipe in its `related` field or within its body, the reference MUST use the sibling's canonical `domain` URI, not its filename, title, or a freeform description.
- Cross-references in the body text MUST be formatted consistently: if one sibling uses `[Button Recipe](agentic-cookbook://recipes/ui/button)`, all siblings MUST use the same link format — not bare URIs in some and formatted links in others.
- Cross-references MUST be verified at review time to ensure the target recipe exists and the domain URI is correct. Broken cross-references are a consistency failure.
- When a new recipe is added that is relevant to an existing recipe, the existing recipe's `related` field SHOULD be updated to include the new entry. Unidirectional cross-references are acceptable but bidirectional is preferred.

## Common Violations

- **Inconsistent entity naming.** A login recipe refers to the authenticated entity as "user". A sibling password-reset recipe refers to the same entity as "account". A profile recipe calls it "member". Consumers reading across the family cannot determine whether these are distinct concepts or synonyms.
- **Wildly different detail levels.** A "Text Input" recipe has 4 behavioral requirements and no state definitions. Its sibling "Select Dropdown" recipe has 22 behavioral requirements, 8 states, and 15 edge cases. Both are simple form controls of comparable complexity. The disparity signals that one recipe received significantly less authoring effort than the other.
- **Inconsistent tag vocabulary.** One recipe uses `error-handling`, a sibling uses `errors`, and a third uses `error-states`. A tag-based search for any one term misses the other two. The cookbook's tag taxonomy is fragmented.
- **Wrong platform identifier casing.** A recipe lists `iOS` in its platforms array. All siblings list `ios`. Automated tools that filter by exact platform name will exclude the inconsistent recipe.
- **Broken cross-reference.** A recipe's `related` field includes `agentic-cookbook://recipes/ui/icon-button`. The `icon-button` recipe was renamed to `icon-action` in a previous version. The reference now points to a nonexistent artifact.
- **Unidirectional reference when bidirectional is expected.** Recipe A lists Recipe B in its `related` field. Recipe B has no reference back to Recipe A. A developer reading Recipe B has no way to discover the connection without searching the cookbook.
- **Non-canonical term introduced without justification.** All recipes in a forms family use "validation error" for inline error messages. A new recipe introduces "field-level feedback" for the same concept. No Design Decisions entry explains why a new term was needed.

## Verification Checklist

A verifier MUST check each of the following items. The recipe PASSES cross-recipe consistency only if every item is satisfied.

- [ ] All terms for shared concepts match the terminology used in sibling recipes.
- [ ] No synonym for an established term is introduced without a documented justification in Design Decisions.
- [ ] Section depth (number of behavioral requirements, states, edge cases) is comparable to sibling recipes of similar complexity, or a documented rationale explains the disparity.
- [ ] All tags use the family's established tag vocabulary — no freeform or ad-hoc tags not used by siblings.
- [ ] Platform identifiers use the cookbook's canonical casing and naming.
- [ ] The `author` field format matches the convention established in the family.
- [ ] All cross-references use canonical `domain` URIs, not filenames or titles.
- [ ] Cross-reference link formatting is consistent with siblings (formatted links vs. bare URIs).
- [ ] All cross-referenced domain URIs resolve to existing recipes in the cookbook.
- [ ] Existing related recipes have been updated to include a reference back to this recipe where appropriate.

## Change History
