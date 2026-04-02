# Software Architecture Specialist

## Domain Coverage
Composition, dependency injection, boundaries, separation of concerns, modularity, testability, optimize for change.

## Cookbook Sources
- `cookbook/principles/composition-over-inheritance.md`
- `cookbook/principles/dependency-injection.md`
- `cookbook/principles/manage-complexity-through-boundaries.md`
- `cookbook/principles/separation-of-concerns.md`
- `cookbook/principles/meta-principle-optimize-for-change.md`

## Structured Questions

1. Walk me through the major subsystems of your app. Where's the boundary between UI, business logic, and data access?

2. If you needed to swap your database tomorrow, what code would change? Is business logic coupled to queries, or behind an abstraction?

3. How do you pass dependencies into components and services? Constructor injection, service locator, or something else?

4. Your app has a feature involving UI, business logic, and a third-party API. Walk me through data flow from API through layers to screen. Where's validation? Transformation?

5. Describe a piece of business logic. Can you test it without a database? Without rendering UI? How?

6. Two features share 70% of code. Inheritance, composition, or something else?

7. Your app uses a third-party library. How do you isolate your code from changes to that API? Adapter, or direct calls from multiple places?

8. A developer adds a feature and modifies 8 modules. How would you know that signals a problem?

9. If I look at your codebase in six months, what changes will be easy? What will be painful? Did you design for the easy ones intentionally?

10. Your app needs multiple data sources (local DB, remote API, cached files). How do you abstract so business logic doesn't care which one?

11. How do errors propagate across layers? Does a database error bubble to UI as a raw exception, or transformed into a domain error?

12. Can you inject a logging service, or is logging scattered? What would refactoring look like?

13. A component fetches, processes, and renders data. Is that one thing or three? If you needed the processed data in a different UI, what would you do?

14. How do you define a "module" — folder, class, package, service? What makes something cohesive?

15. If business rules change, what's the blast radius? Would a pricing change affect the UI layer, data layer, or neither?

## Exploratory Prompts

1. If you had to rewrite your app but keep one module as-is, which would it be and why?

2. What if your business logic had to run in three environments — web, mobile, and a backend worker? How would that change your architecture?

3. If you discovered a bug in core business logic affecting thousands of users, how would you fix it with confidence?

4. Why does a particular piece of logic live where it does? What would it look like somewhere else?
