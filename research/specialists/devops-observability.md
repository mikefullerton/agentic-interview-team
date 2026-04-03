# DevOps & Observability Specialist

## Domain Coverage
Structured logging, analytics, tight feedback loops, performance compliance, debug mode, deploy process, feature flags (operational), monitoring.

## Cookbook Sources
- `guidelines/logging/`
- `principles/tight-feedback-loops.md`
- `compliance/performance.md`
- `guidelines/feature-management/feature-flags.md`
- `guidelines/feature-management/ab-testing.md`
- `guidelines/feature-management/debug-mode.md`

## Structured Questions

1. Walk me through what happens from a user action to when you see it in monitoring. Which layers are instrumented? Which are dark?

2. How do you debug production issues? What logs do you have? How much of the user's journey can you reconstruct?

3. User reports "things are slow." How do you find the bottleneck? Distributed tracing? Can you correlate frontend with backend?

4. What's your logging strategy? Structured (JSON with typed fields) or unstructured strings? Can you query efficiently?

5. Describe your deploy process. How often? How many changes go out together? How do you catch regressions?

6. How are feature flags managed? Hardcoded, config file, or server-driven? Can you toggle for a subset of users without deploying?

7. What's your relationship with analytics? Tracking events hardcoded or abstracted behind an interface? How coupled to a specific backend?

8. If you wanted to experiment with a new feature for 10% of users, what would that take? How long?

9. What does debug mode look like? Can devs/QA override flags, check build version, inspect internal state?

10. How fast are your tests? If 30 minutes, do developers run locally or rely on CI?

11. Describe your performance baselines. Startup time, frame rates, memory usage — do you measure them? How do you know if a change made things slower?

12. How do you handle observability in dev vs. production? Different logs? Analytics? Can developers test instrumentation before deploying?

## Exploratory Prompts

1. What if you could see every user interaction in real time (with permission)? How would that change your product understanding?

2. What's the gap between "what we measure" and "what we care about"? Metrics that don't matter? Things that matter but can't be measured?

3. If your feedback loop got 10x faster, what would you do differently?

4. What's the cost of a slow test run or slow deploy? How does that manifest in developer behavior?
