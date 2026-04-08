# Specialist Assignment Rules

Determines which specialists review or augment each recipe. Used by the generate, build, and lint skills.

## Assignment Logic

For each recipe, assign specialists based on three criteria applied in order:

### 1. Recipe Category → Domain Specialists

| Category Pattern | Specialists |
|-----------------|------------|
| `recipe.ui.*` | UI/UX & Design, Accessibility |
| `recipe.infrastructure.*` | Software Architecture, Code Quality |
| `recipe.app.*` | Software Architecture, Development Process |
| All recipes with behavioral requirements | Reliability & Error Handling |

### 2. Recipe Content → Additional Specialists

Scan the recipe for keywords and add specialists:

| Keywords | Specialist |
|----------|-----------|
| auth, tokens, credentials | Security |
| network, API, endpoint, HTTP | Networking & API |
| storage, persistence, database, cache | Data & Persistence |
| logging, analytics, monitoring | DevOps & Observability |
| localization, i18n, RTL, locale | Localization & I18n |
| test, testing, verification | Testing & QA |
| claude, skill, rule, agent, hook, MCP | Claude Code & Agentic Development |

### 3. Project Platforms → Platform Specialists

From `cookbook-project.json` `platforms` array:

| Platform | Specialist |
|----------|-----------|
| ios, macos | platform-ios-apple |
| android | platform-android |
| windows | platform-windows |
| web | platform-web-frontend, platform-web-backend |

### 4. Universal Specialists

These specialists are assigned to **every recipe** regardless of category, content, or platform:

| Specialist | Reason |
|-----------|--------|
| Recipe | Meta-quality: template conformance, behavioral requirement rigor, source fidelity, completeness, cross-recipe consistency |

### Limits

Assign at most **3-4 specialists per recipe** (not counting universal specialists). Priority: domain specialist most related to recipe category → platform specialists → cross-cutting specialists.

## Specialist Tier Ordering (Build Only)

When specialists augment code sequentially in the build workflow, order by tier:

| Tier | Role | Specialists |
|------|------|------------|
| 1 | Foundation | software-architecture |
| 2 | Core Domain | reliability, data-persistence, networking-api |
| 3 | Cross-Cutting | security, ui-ux-design, accessibility, localization-i18n, testing-qa, devops-observability, code-quality, development-process, claude-code, recipe |
| 4 | Platform | platform-ios-apple, platform-android, platform-windows, platform-web-frontend, platform-web-backend, platform-database |
