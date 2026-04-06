# Database Research

Reference library for database schema design, performance, sync strategies, and production operations. Organized by topic for use in:

1. **Schema planning** — analyzing and improving database schemas for data access patterns, speed, search, resilience, and flexibility
2. **Sync architecture** — planning server DBs, local DBs, and the synchronization strategy between them

## Documents

### Core (SQLite-focused)

| Document | Description |
|----------|-------------|
| [Schema Design](schema-design.md) | Column naming, data types, primary keys, foreign keys, constraints, and design patterns |
| [Performance and Tuning](performance-and-tuning.md) | Indexes, triggers, WAL mode, transactions, query optimization, PRAGMA settings |
| [Operations and Maintenance](operations-and-maintenance.md) | Migrations, backup/recovery, date handling, blob storage, security, testing, anti-patterns |

### Sync

| Document | Description |
|----------|-------------|
| [Sync Strategies](sync-strategies.md) | Database-agnostic: conflict resolution, sync protocols, offline-first architecture, clock systems, sync engine design |
| [SQLite Sync Implementation](sync-sqlite.md) | SQLite-specific: schema for sync, type mapping, tools/extensions (cr-sqlite, PowerSync, ElectricSQL, Turso, Litestream), performance tuning |
| [Sync Case Studies](sync-case-studies.md) | Real-world architectures: Notion, Linear, Figma, Temporal, mobile/desktop patterns |
| [Decision Frameworks](decision-frameworks.md) | Decision trees: choosing sync strategy, sync tool, clock system, conflict resolution, schema patterns |

## Cross-References

- **Planning server + local DBs**: Start with [Decision Frameworks](decision-frameworks.md) → [Sync Strategies](sync-strategies.md) → [SQLite Sync Implementation](sync-sqlite.md)
- **Schema review**: Start with [Schema Design](schema-design.md) → [Decision Frameworks](decision-frameworks.md) § Schema Design Pattern Selection
- **Performance investigation**: [Performance and Tuning](performance-and-tuning.md) → [SQLite Sync Implementation](sync-sqlite.md) § Performance Considerations

## Origin

Split from the original monolithic `sqlite-best-practices.md` (April 2026) plus new sync strategy research drawn from the Temporal project's production sync engine implementation.
