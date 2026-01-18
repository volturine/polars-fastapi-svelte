# Database Documentation

Complete documentation for the database layer of the Polars-FastAPI-Svelte Analysis Platform.

## Overview

The application uses **SQLite** with async support via **aiosqlite** and **SQLAlchemy 2.0+**. Database migrations are managed with **Alembic**.

## Contents

| Document | Description |
|----------|-------------|
| [Setup](./setup.md) | Database configuration and initialization |
| [Models](./models.md) | SQLAlchemy ORM models |
| [Migrations](./migrations.md) | Alembic migration system |
| [Queries](./queries.md) | Common query patterns |

## Quick Reference

### Database URL

```python
# Default (SQLite)
database_url = 'sqlite+aiosqlite:///./database/app.db'
```

### Tables

| Table | Description |
|-------|-------------|
| `analyses` | Analysis metadata and pipeline definitions |
| `datasources` | Data source configurations |
| `analysis_datasources` | Many-to-many junction table |
| `alembic_version` | Migration tracking |

### Entity Relationships

```
datasources ─────────┐
                     │ M:N
                     ▼
              analysis_datasources
                     ▲
                     │ M:N
analyses ────────────┘
```

## Database File Location

```
backend/
├── database/
│   ├── app.db           # SQLite database file
│   ├── alembic.ini      # Alembic configuration
│   └── alembic/         # Migration versions
│       ├── env.py
│       └── versions/
```

## Key Features

- **Async Support**: All operations use async/await
- **Type Safety**: SQLAlchemy 2.0 Mapped types
- **JSON Columns**: Native JSON storage for configs
- **Cascade Deletes**: Automatic cleanup of related records
- **Migration Support**: Version-controlled schema changes

## See Also

- [Setup](./setup.md) - Database configuration
- [Models](./models.md) - ORM model documentation
- [Migrations](./migrations.md) - Migration guide
- [Queries](./queries.md) - Query patterns
