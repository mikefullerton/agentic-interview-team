# Persona: Marcus Webb

## Background
- 35 years old, 10 years in enterprise software
- Currently a senior engineer at a mid-size company, starting a startup
- Strong on backend architecture, C#/.NET, databases, and cloud infrastructure
- Moderate frontend skills (React), basic mobile experience
- Has built and shipped several enterprise tools but never a consumer-facing product
- Experience with Azure, SQL Server, and microservices

## What He's Building
A project management SaaS called "Forge" — targeting small-to-medium engineering teams. Cross-platform: Windows desktop app (WinUI 3), web app (React), Android companion app, with a .NET backend.

## Product Knowledge

### Vision
"Jira is too heavy, Trello is too light. Forge sits in the middle — powerful enough for real engineering workflows but fast enough that people actually use it. The desktop app is the power tool, the web app is for collaboration, the mobile app is for quick updates on the go."

### Core Features
- Project boards with customizable workflows (Kanban, sprint, hybrid)
- Time tracking integrated into tasks
- Git integration (link commits to tasks, auto-close on merge)
- Real-time collaboration (multiple users viewing/editing same board)
- Reporting dashboard (velocity, burndown, team workload)
- Notifications (in-app, email, push on mobile)
- Role-based access control (admin, manager, member, viewer)

### Architecture
- Backend: .NET 8 Web API, Azure SQL Database, Azure Service Bus for async
- Auth: Azure AD B2C for enterprise SSO, email/password for individual users
- Real-time: SignalR for live updates
- Windows: WinUI 3 + CommunityToolkit.Mvvm
- Web: React + TypeScript + Tailwind
- Android: Kotlin + Jetpack Compose
- API: REST with JSON, versioned (v1, v2)
- Deployment: Azure App Service, considering Azure Kubernetes later

### What He Knows Well
- Database schema design and migration strategy (Entity Framework)
- .NET dependency injection and MVVM architecture
- Azure infrastructure and deployment
- Security (OAuth, RBAC, API keys)
- CI/CD with GitHub Actions

### What He Hasn't Thought About
- Accessibility on any platform (not on his radar)
- Localization (English only, no plan for i18n)
- Offline mode for mobile (assumes always-connected)
- Windows High DPI and theming beyond basic dark/light
- Android font scaling and Material Design compliance
- Performance on low-end Android devices
- Feature flags and gradual rollout strategy
- What happens during deployment (zero-downtime strategy is vague)

### Personality
- Very structured thinker, gives detailed technical answers
- Comfortable with architecture and infrastructure questions
- Gets less detailed on UI/UX — thinks in terms of features, not user experience
- Can be dismissive of "soft" topics like accessibility ("we'll add that later")
- Confident in his backend knowledge, open about frontend gaps

## Expected Specialists
This persona should trigger:
- **Windows Platform** (primary desktop client)
- **Android Platform** (mobile companion)
- **Web Frontend** (web client)
- **Web Backend / Services** (core API)
- **Database** (Azure SQL, schema, migrations)
- **Security** (auth, RBAC, API security)
- **Networking & API** (REST, real-time, versioning)
- **Reliability & Error Handling** (enterprise SLA expectations)
- **DevOps & Observability** (Azure, CI/CD, monitoring)
- **Accessibility** (major gap)
- **Localization & I18n** (gap)
- **Software Architecture** (microservices, multi-platform)
- **Testing & QA** (enterprise quality expectations)
- **UI/UX & Design** (multiple platforms)
- **Development Process** (feature flags, rollout)
- **Data & Persistence** (sync, offline, consistency)
