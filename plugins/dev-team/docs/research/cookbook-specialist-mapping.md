# Cookbook-to-Specialist Domain Mapping

Maps every principle, guideline topic, and compliance category from the agentic-cookbook to the specialist domains defined in the interview system.

## Principles (18) → Specialist Domains

| Principle | Specialist Domain |
|-----------|------------------|
| Composition over inheritance | Software Architecture |
| Dependency injection | Software Architecture |
| Design for deletion | Code Quality & Maintainability |
| Explicit over implicit | Code Quality & Maintainability |
| Fail fast | Reliability & Error Handling |
| Idempotency | Reliability & Error Handling / Data & Persistence |
| Immutability by default | Software Architecture / Concurrency |
| Make It Work, Make It Right, Make It Fast | Development Process & Product |
| Manage complexity through boundaries | Software Architecture |
| Meta-Principle: Optimize for Change | Software Architecture |
| Prefer native controls and libraries | Platform Specialists (all) |
| Prefer proven open-source solutions | Software Architecture / Code Quality |
| Principle of least astonishment | UI/UX & Design / API Design |
| Separation of concerns | Software Architecture |
| Simplicity | Code Quality & Maintainability |
| Small, reversible decisions | Development Process & Product |
| Tight feedback loops | DevOps & Observability |
| Support automation | Claude Code & Agentic Development |
| YAGNI | Development Process & Product |

## Guideline Topics (14+) → Specialist Domains

| Guideline Topic | Sub-Topics | Specialist Domain |
|-----------------|------------|------------------|
| Accessibility | Accessibility from day one | Accessibility |
| Code Quality | Scope discipline, Linting, Atomic commits, Bulk operations | Code Quality & Maintainability |
| Concurrency | Immutability, No blocking main thread | Software Architecture |
| Feature Management | Feature flags, A/B testing, Debug mode | Development Process & Product |
| Internationalization | Localizability, RTL layout | Localization & I18n |
| Logging | Analytics, Instrumented logging | DevOps & Observability |
| Networking | Retry, Caching, Pagination, API Design, Rate Limiting, Offline, Error Responses, Timeouts, Real-Time | Networking & API |
| Security | Auth, Transport, Dependencies, Tokens, Authorization, Privacy, Headers, Storage, CORS, CSP, Input Validation | Security |
| Skills and Agents | Authoring skills and rules, Performance | Claude Code & Agentic Development |
| Testing | Verification, Test Data, Unit Patterns, Properties, Mutation, Property-Based, Workflow, Flaky Prevention, Pyramid, Doubles, Security Testing | Testing & QA |
| UI | Scriptable, Deep linking, Icons, Feedback, Visual Hierarchy, State, Animation, Platform Design Languages, Color, Forms, Spacing, Typography, Touch Targets, Progress, Previews, Layout, Data Display | UI/UX & Design |

### Language-Specific Guidelines → Platform Specialists

| Language | Guidelines | Platform Specialist |
|----------|-----------|-------------------|
| Swift | Dynamic Type | iOS/Apple Platform |
| Kotlin | Font Scaling | Android Platform |
| C# | Nullable References, DI, Naming | Windows/.NET Platform |
| Python | Type hints, Web services, File paths, Database | Web Backend Platform |

### Platform-Specific Guidelines

| Platform | Guidelines | Platform Specialist |
|----------|-----------|-------------------|
| Windows | Architecture, Notifications, High DPI, Theming, MSIX, Design-Time Data, Fluent Design | Windows Platform |

## Compliance Categories (10) → Specialist Domains

| Compliance Category | Specialist Domain |
|--------------------|------------------|
| Access Patterns | Networking & API |
| Accessibility | Accessibility |
| Best Practices | Code Quality & Maintainability |
| Internationalization | Localization & I18n |
| Performance | DevOps & Observability |
| Platform Compliance | Platform Specialists (all) |
| Privacy and Data | Security / Data & Persistence |
| Reliability | Reliability & Error Handling |
| Security Compliance | Security |
| User Safety | Security |

## Proposed Specialist Roster

### Domain Specialists (12)

1. **Security** — auth, transport, storage, input validation, privacy, CORS, CSP
2. **UI/UX & Design** — layout, color, typography, animation, forms, visual hierarchy, feedback patterns
3. **Accessibility** — screen readers, keyboard nav, dynamic type, contrast, touch targets, reduced motion
4. **Software Architecture** — composition, DI, boundaries, separation of concerns, immutability
5. **Code Quality & Maintainability** — simplicity, deletability, linting, atomic commits, explicit code
6. **Testing & QA** — test pyramid, test doubles, mutation testing, flaky prevention, security testing
7. **Networking & API** — API design, caching, pagination, rate limiting, offline, retry, timeouts
8. **DevOps & Observability** — logging, analytics, monitoring, feedback loops, performance
9. **Localization & I18n** — localizability, RTL, cultural adaptation
10. **Reliability & Error Handling** — fail fast, idempotency, error responses, recovery
11. **Development Process & Product** — feature flags, A/B testing, iterative development, YAGNI
12. **Data & Persistence** — storage, sync, conflict resolution, migration, offline data
13. **Claude Code & Agentic Development** — plugin architecture, skill/rule/agent authoring, hooks, MCP servers, context management, performance optimization, multi-agent orchestration

### Platform Specialists (6)

1. **iOS / Apple Platforms** — UIKit, SwiftUI, App Store, HIG, Dynamic Type, all Apple platforms
2. **Android** — Kotlin, Material Design, font scaling, Play Store
3. **Windows** — WinUI, Fluent Design, MSIX, High DPI, .NET
4. **Web Frontend** — HTML/CSS/JS, frameworks, responsive design, browser APIs
5. **Web Backend / Services** — APIs, middleware, scaling, deployment
6. **Database** — schema design, migrations, indexing, geoscaling, failover

## Coverage Analysis

Every cookbook principle, guideline topic, and compliance category maps to at least one specialist. The 19 specialists (13 domain + 6 platform) provide complete coverage with room to grow.

Specialists that cover the most cookbook content:
- **Software Architecture** — 5 principles, concurrency guidelines
- **Security** — 12+ security guidelines, 3 compliance categories
- **UI/UX & Design** — 17+ UI guidelines, platform design languages
- **Platform Specialists** — platform-specific guidelines + compliance
