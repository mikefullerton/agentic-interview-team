# DB Schema Design Rules

When designing or modifying database tables, follow these rules:

1. **No blobs** — Don't store summaries, narratives, or unstructured text in columns. If you wouldn't filter, join, or sort on it, it doesn't belong.

2. **No computed values** — Don't store counts, totals, or derived booleans. Query the rows to get counts. Derive pass/fail from the data.

3. **No unstructured lists** — If a column would hold a list, make it a separate table with one row per item.

4. **Columns must be indexable and searchable** — Before adding any column, ask: "Would I WHERE, JOIN, or ORDER BY this?" If no, it doesn't belong.

5. **Meaningful names** — No `parent_id` (use the actual FK name like `session_id`). No `_at` suffixes (use `creation_date`, `modification_date`). No vague terms like `component`.

6. **Use project vocabulary** — Column and table names must match established terminology (team-lead, specialist, specialty-team, etc.), not generic terms.

7. **Flexible tables over predicted columns** — When you can't predict all uses, use a general table with a `type` column (e.g., `paths` table instead of `repo_path`, `project_path` columns).

8. **Separate tables over sparse nullable columns** — If a column would be NULL for most rows, the data belongs in a child table where every row is meaningful. Test: if a column only applies to one type/category of row, it's a separate table.

9. **Tables serve searching** — SQL tables are structured data in service of searching. Design for queries, not document storage.
