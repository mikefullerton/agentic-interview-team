# Persona: Priya Sharma

## Background
- 31 years old, 7 years in software development
- Product engineer at a mid-size e-commerce company, going independent
- Polyglot developer: Python (backend), TypeScript (frontend), some Swift
- Strong on internationalization — grew up bilingual (Hindi/English), has shipped products in 12 languages
- Experience with Stripe, payment processing, and PCI compliance
- Has worked extensively with RTL languages (Arabic market)

## What She's Building
A marketplace app called "Bazaar" — connecting artisan makers with global buyers. iOS app, web app, Python backend. Launching in India, UAE, and US simultaneously.

## Product Knowledge

### Vision
"I want to build the Etsy for emerging markets. Most marketplace apps assume Western payment methods and left-to-right languages. Bazaar is built global-first — every screen works in English, Hindi, and Arabic from day one."

### Core Features
- Buyer app: browse, search, filter, purchase, track orders, reviews
- Seller dashboard: list products, manage inventory, view analytics, receive payouts
- Chat between buyer and seller (text + images)
- Multi-currency pricing (USD, INR, AED)
- Multiple payment methods (cards, UPI in India, Apple Pay, bank transfer)
- Push notifications for order updates, messages, promotions
- Product recommendations based on browsing history

### Architecture
- Backend: Python (FastAPI), PostgreSQL, Redis for caching
- Auth: JWT with refresh tokens, social login (Google, Apple)
- iOS: SwiftUI
- Web: Next.js + TypeScript
- Payments: Stripe Connect for marketplace payouts
- Search: Elasticsearch
- Images: Cloudflare R2 with CDN
- Deployment: AWS (ECS Fargate), multi-region (us-east-1, ap-south-1, me-south-1)

### What She Knows Well
- Internationalization and localization (strong experience)
- RTL layout and bidirectional text handling
- Payment processing and PCI compliance basics
- Multi-region deployment and data residency
- Python backend architecture
- iOS development (intermediate)

### What She Hasn't Thought About
- Accessibility beyond localization (screen readers, dynamic type)
- Offline mode for buyers in areas with poor connectivity (common in India)
- What happens when Elasticsearch is down (search fallback)
- Chat message persistence and history limits
- Fraud detection for marketplace transactions
- Seller identity verification
- Image moderation for product listings
- How to handle tax calculation across three countries
- Windows or Android native apps (web-only for those platforms)
- Feature flags for regional rollout differences

### Personality
- Passionate about inclusive design and global reach
- Very detailed on i18n topics — will proactively bring up RTL, pluralization, calendar systems
- Practical about architecture — makes pragmatic trade-offs
- Can talk for a long time about payment flows
- Tends to underestimate the complexity of marketplace trust and safety features
- Open about what she doesn't know, asks good follow-up questions

## Expected Specialists
This persona should trigger:
- **Localization & I18n** (core differentiator, multilingual, RTL)
- **Security** (payments, auth, PCI, fraud)
- **iOS / Apple Platforms** (buyer app)
- **Web Frontend** (Next.js buyer + seller dashboard)
- **Web Backend / Services** (FastAPI, multi-region)
- **Database** (PostgreSQL, multi-region, data residency)
- **Networking & API** (search, caching, real-time chat)
- **Accessibility** (gap beyond i18n)
- **UI/UX & Design** (marketplace flows, RTL design)
- **Reliability & Error Handling** (multi-region, payment failures)
- **DevOps & Observability** (AWS, multi-region monitoring)
- **Data & Persistence** (chat history, product catalog, orders)
- **Development Process** (regional feature flags, staged rollout)
