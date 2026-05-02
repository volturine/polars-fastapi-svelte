---
name: sqlite
description: Generic Python-first workflow for inspecting, querying, and updating SQLite databases safely. Use when the user wants to explore a `.db` or `.sqlite` file, inspect schema, run ad hoc queries, export results, apply schema changes, debug data issues, or work with FTS and indexes using Python's built-in `sqlite3` module.
---

# SQLite

Use Python's standard `sqlite3` module for all SQLite interaction unless the user explicitly asks for another interface.

Keep operations safe, inspectable, and easy to repeat.

## Runtime Inputs

- Path to the SQLite database file
- Optional SQL query or schema change
- Optional output path for exported results

## Automation

- Inspect schema and table stats: `python3 <skill-dir>/scripts/inspect_db.py <db-path>`
- Run a read query: `python3 <skill-dir>/scripts/run_query.py <db-path> <sql> [params-json]`
- Export a query to CSV: `python3 <skill-dir>/scripts/export_csv.py <db-path> <sql> <output-csv> [params-json]`
- Apply SQL statements from a file: `python3 <skill-dir>/scripts/apply_sql.py <db-path> <sql-file>`

Read these references when needed:

- `references/security-examples.md`: parameter binding, safe dynamic SQL patterns, and validation rules
- `references/advanced-patterns.md`: FTS5, indexes, WAL mode, query planning, and migration patterns

## Workflow

1. Inspect the database before changing it.
2. Prefer read-only exploration first: tables, schema, row counts, indexes.
3. Use parameterized queries for any user-provided values.
4. Wrap related write operations in a transaction.
5. Re-inspect the changed schema or data after writes.

## Common Tasks

### Explore a database

- list tables
- inspect schema
- inspect indexes
- count rows
- preview sample rows

Use `inspect_db.py` first when the database structure is not yet known.

### Run ad hoc analysis

- use `run_query.py`
- pass parameters as JSON arrays or objects when values come from user input
- keep queries read-only unless the user explicitly asked for writes

### Export data

- use `export_csv.py` for query results that should leave the database
- keep the query explicit so the export is reproducible

### Apply schema or data changes

- put the SQL into a file
- apply it with `apply_sql.py`
- verify the result with `inspect_db.py` or a follow-up query

## Rules

- Use Python and `sqlite3`, not product-specific database wrappers.
- Never concatenate user-provided values directly into SQL.
- Treat identifiers like table or column names separately from values; whitelist them before interpolation.
- Turn on `PRAGMA foreign_keys = ON` for write operations.
- Prefer explicit SQL files for multi-statement schema changes.
- Explain the risk before running destructive statements such as `DROP`, `DELETE`, or mass `UPDATE`.

## Output

Report:

1. What database was inspected or changed
2. What query or change ran
3. What the result means
4. Any follow-up risk or verification step
