# Database Models

Complete documentation for all SQLAlchemy ORM models.

## Base Configuration

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import JSON, DateTime

class Base(DeclarativeBase):
    """Base class for all models."""
    type_annotation_map = {
        dict: JSON,
        datetime: DateTime(timezone=True),
    }
```

**Type Mappings**:
- `dict` → `JSON` column
- `datetime` → `DateTime` with timezone

---

## DataSource Model

**Table**: `datasources`

```python
class DataSource(Base):
    __tablename__ = 'datasources'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    schema_cache: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
```

### Fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | VARCHAR | No (PK) | UUID primary key |
| `name` | VARCHAR | No | User-provided name |
| `source_type` | VARCHAR | No | `file`, `database`, `api` |
| `config` | JSON | No | Source-specific configuration |
| `schema_cache` | JSON | Yes | Cached schema information |
| `created_at` | DATETIME | No | Creation timestamp (TZ) |

### Config Schema (File)

```json
{
  "file_path": "./data/uploads/uuid.csv",
  "file_type": "csv",
  "options": {}
}
```

### Config Schema (Database)

```json
{
  "connection_string": "postgresql://...",
  "query": "SELECT * FROM users"
}
```

### Config Schema (API)

```json
{
  "url": "https://api.example.com/data",
  "method": "GET",
  "headers": {},
  "auth": {}
}
```

---

## Analysis Model

**Table**: `analyses`

```python
class Analysis(Base):
    __tablename__ = 'analyses'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    pipeline_definition: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String, default='draft')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    result_path: Mapped[str | None] = mapped_column(String, nullable=True)
    thumbnail: Mapped[str | None] = mapped_column(String, nullable=True)
```

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | VARCHAR | No (PK) | - | UUID primary key |
| `name` | VARCHAR | No | - | Analysis name |
| `description` | VARCHAR | Yes | NULL | Optional description |
| `pipeline_definition` | JSON | No | - | Steps, datasources, tabs |
| `status` | VARCHAR | No | `'draft'` | Execution status |
| `created_at` | DATETIME | No | - | Creation timestamp |
| `updated_at` | DATETIME | No | - | Last update timestamp |
| `result_path` | VARCHAR | Yes | NULL | Path to result file |
| `thumbnail` | VARCHAR | Yes | NULL | Preview thumbnail |

### Status Values

- `draft` - Not yet executed
- `running` - Currently executing
- `completed` - Execution successful
- `failed` - Execution failed

### Pipeline Definition Schema

```json
{
  "steps": [
    {
      "id": "step-uuid",
      "type": "filter",
      "config": {...},
      "depends_on": []
    }
  ],
  "datasource_ids": ["ds-uuid"],
  "tabs": [
    {
      "id": "tab-uuid",
      "name": "Tab Name",
      "type": "datasource",
      "parent_id": null,
      "datasource_id": "ds-uuid",
      "steps": [...]
    }
  ]
}
```

---

## AnalysisDataSource Model (Junction)

**Table**: `analysis_datasources`

```python
class AnalysisDataSource(Base):
    __tablename__ = 'analysis_datasources'

    analysis_id: Mapped[str] = mapped_column(
        String,
        ForeignKey('analyses.id', ondelete='CASCADE'),
        primary_key=True
    )
    datasource_id: Mapped[str] = mapped_column(
        String,
        ForeignKey('datasources.id', ondelete='CASCADE'),
        primary_key=True
    )
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `analysis_id` | VARCHAR (FK, PK) | References analyses.id |
| `datasource_id` | VARCHAR (FK, PK) | References datasources.id |

### Cascade Behavior

- Delete Analysis → Deletes all AnalysisDataSource records
- Delete DataSource → Deletes all AnalysisDataSource records

---

## Entity Relationship Diagram

```
┌─────────────────────────────┐
│        datasources          │
├─────────────────────────────┤
│ id          VARCHAR (PK)    │
│ name        VARCHAR         │
│ source_type VARCHAR         │
│ config      JSON            │
│ schema_cache JSON NULL      │
│ created_at  DATETIME        │
└──────────────┬──────────────┘
               │
               │ 1:N
               ▼
┌─────────────────────────────┐
│   analysis_datasources      │
├─────────────────────────────┤
│ datasource_id VARCHAR (FK,PK)│◄─┐
│ analysis_id   VARCHAR (FK,PK)│  │
└──────────────┬──────────────┘  │
               │                 │
               │ N:1             │
               ▼                 │
┌─────────────────────────────┐  │
│         analyses            │  │
├─────────────────────────────┤  │
│ id          VARCHAR (PK)    │──┘
│ name        VARCHAR         │
│ description VARCHAR NULL    │
│ pipeline_definition JSON    │
│ status      VARCHAR         │
│ created_at  DATETIME        │
│ updated_at  DATETIME        │
│ result_path VARCHAR NULL    │
│ thumbnail   VARCHAR NULL    │
└─────────────────────────────┘
```

---

## See Also

- [Setup](./setup.md) - Database configuration
- [Migrations](./migrations.md) - Schema migrations
- [Queries](./queries.md) - Common queries
