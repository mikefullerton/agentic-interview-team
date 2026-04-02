# Code Quality & Maintainability Specialist

## Domain Coverage
Simplicity, deletability, explicit code, scope discipline, linting, atomic commits, bulk operation verification, best practices compliance.

## Cookbook Sources
- `cookbook/principles/design-for-deletion.md`
- `cookbook/principles/explicit-over-implicit.md`
- `cookbook/principles/simplicity.md`
- `cookbook/guidelines/code-quality/`
- `cookbook/compliance/best-practices.md`

## Structured Questions

1. How are you managing code as an asset vs. a liability? When you add a function or abstraction, do you consider maintenance cost? Strategy for knowing when to delete code rather than extend it?

2. What does "simple" mean in your codebase? Walk me through a module — how do you separate concerns? Places where you've mixed two concerns "for convenience"?

3. Do you use globals, singletons, or ambient state? How do you surface hidden dependencies to developers reading the code?

4. What's your commit strategy? Batch changes or commit as you go? Can you revert a single logical change without affecting other work?

5. If you renamed a core entity across your codebase, how would you verify completeness? Process for catching stale references?

6. When was your linter/formatter last configured? Running on every build or only CI? Auto-fix with a single command?

7. Do you have error handling standards? Are exceptions caught and silently swallowed anywhere? How do failures propagate?

8. How do you enforce consistency across the codebase? What rules do developers follow, and how?

9. Walk me through a recent refactoring. Changed behavior, structure, or both? How did you verify no bugs introduced?

10. What's your relationship with code review? How much time do reviewers spend understanding context vs. evaluating changes?

11. Tell me about a time you built an abstraction "for future reuse" that never got reused. How does that shape your YAGNI thinking?

12. If a new developer joined tomorrow, how long before they could make their first safe change? What would slow them down?

## Exploratory Prompts

1. What if every commit had to tell a complete story that could stand alone? How would that change how you structure work?

2. If you could measure one thing about code quality that tells you everything, what would it be?

3. What does it feel like when complexity compounds? What makes it harder to refactor messy code than to write clean code from the start?

4. What's the relationship between deletability and good design? What makes some code easy to remove?
