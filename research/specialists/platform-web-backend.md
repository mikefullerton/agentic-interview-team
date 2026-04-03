# Web Backend / Services Platform Specialist

## Domain Coverage
APIs, middleware, scaling, deployment, databases, authentication services, caching layers, message queues, microservices vs. monolith.

## Cookbook Sources
- `guidelines/networking/`
- `guidelines/security/`
- `guidelines/language/python/`
- `compliance/reliability.md`
- `compliance/access-patterns.md`
- `compliance/security.md`

## Structured Questions

1. What's your backend architecture — monolith, microservices, serverless, or a mix? Why?

2. What language/framework is your backend built with? What drove that choice?

3. How do you handle authentication on the backend? JWT validation, session management, or something else?

4. Describe your database architecture. Single database? Read replicas? Sharding? What drives those decisions?

5. How do you handle caching? What layer (CDN, application cache, database cache)? Invalidation strategy?

6. What's your deployment strategy — containers, serverless functions, VMs? How do you handle zero-downtime deploys?

7. How do you scale? Horizontal (more instances) or vertical (bigger machines)? Auto-scaling? What triggers scaling?

8. Describe your message queue / async processing setup if any. What tasks are async vs. synchronous?

9. How do you handle database migrations in production? Backwards-compatible? Blue-green?

10. What's your monitoring and alerting setup? What metrics trigger alerts? Who gets paged?

11. How do you manage environment configuration — secrets, API keys, feature flags? Vault, env vars, config service?

12. What's your disaster recovery plan? Backups? RTO/RPO targets? Have you tested a restore?

## Exploratory Prompts

1. If your primary database went down for an hour, what happens? Can users still do anything?

2. What if traffic 10x'd overnight? What breaks first? What's your bottleneck?

3. Why monolith / why microservices? What would make you switch?

4. If you had to explain your backend to a new hire in 5 minutes, where would you start? What's the hardest thing to understand?
