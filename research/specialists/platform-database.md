# Database Platform Specialist

## Domain Coverage
Schema design, migrations, indexing, query optimization, geoscaling, failover, replication, backup/restore, data modeling.

## Cookbook Sources
- Cross-cutting: data persistence, reliability, networking/access-patterns

## Structured Questions

1. What database(s) are you using — relational, document, key-value, graph? Why that choice?

2. Describe your data model at a high level. What are the core entities and how do they relate?

3. How do you handle schema migrations? Tooling? Backwards-compatible changes? Rollback strategy?

4. What's your indexing strategy? How do you identify slow queries? Do you have a query performance baseline?

5. How do you handle geographic distribution? Single region? Multi-region? Read replicas close to users?

6. Describe your failover strategy. Primary goes down — what happens? Automatic or manual failover? RPO/RTO targets?

7. What's your backup strategy? Frequency? Point-in-time recovery? Have you tested a restore?

8. How do you handle connection pooling? Max connections? What happens when the pool is exhausted?

9. What's your approach to data partitioning/sharding if applicable? Partition key? How do you handle cross-partition queries?

10. How do you handle soft deletes vs. hard deletes? Audit trails? Data retention policies?

11. What's your approach to database-level security — row-level security, encrypted at rest, encrypted in transit?

12. How do you test database interactions — integration tests with real DB, in-memory DB, mocks?

## Exploratory Prompts

1. If your data model had to support a feature you haven't thought of yet, where would the pain be? What's inflexible?

2. What if you needed to change your primary database technology? What's tightly coupled?

3. If you had to guarantee zero data loss across regions during a network partition, what would you trade off?

4. What's the relationship between your data model and your domain model? Are they the same thing?
