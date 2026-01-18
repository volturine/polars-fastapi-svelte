# Analysis Module

Complete documentation for the Analysis module, which manages analysis entities and their pipeline definitions.

## Overview

The Analysis module provides CRUD operations for analyses and manages the relationship between analyses and data sources.

**Location**: `backend/modules/analysis/`

## Files

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy models: `Analysis`, `AnalysisDataSource` |
| `schemas.py` | Pydantic schemas for requests/responses |
| `routes.py` | FastAPI route handlers |
| `service.py` | Business logic functions |

---

## Models

### Analysis

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

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | String (PK) | UUID primary key |
| `name` | String | Analysis name |
| `description` | String (nullable) | Optional description |
| `pipeline_definition` | JSON | Pipeline steps, datasource IDs, tabs |
| `status` | String | `draft`, `running`, `completed`, `failed` |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |
| `result_path` | String (nullable) | Path to result file |
| `thumbnail` | String (nullable) | Preview thumbnail |

### AnalysisDataSource (Junction Table)

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

**Relationships**:
- Many-to-many between `Analysis` and `DataSource`
- Cascade delete: Deleting analysis removes junction records
- Cascade delete: Deleting datasource removes junction records

---

## Schemas

### AnalysisCreateSchema

```python
class AnalysisCreateSchema(BaseModel):
    name: str
    description: str | None = None
    datasource_ids: list[str]
    pipeline_steps: list[PipelineStepSchema] = []
    tabs: list[TabSchema] = []
```

### AnalysisUpdateSchema

```python
class AnalysisUpdateSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    pipeline_steps: list[PipelineStepSchema] | None = None
    status: str | None = None
    tabs: list[TabSchema] | None = None
```

### AnalysisResponseSchema

```python
class AnalysisResponseSchema(BaseModel):
    id: str
    name: str
    description: str | None
    pipeline_definition: dict
    status: str
    created_at: datetime
    updated_at: datetime
    result_path: str | None
    thumbnail: str | None
    tabs: list[TabSchema]

    model_config = ConfigDict(from_attributes=True)
```

### AnalysisGalleryItemSchema

```python
class AnalysisGalleryItemSchema(BaseModel):
    id: str
    name: str
    thumbnail: str | None
    created_at: datetime
    updated_at: datetime
    row_count: int | None
    column_count: int | None
```

### PipelineStepSchema

```python
class PipelineStepSchema(BaseModel):
    id: str
    type: str
    config: dict
    depends_on: list[str] = []
```

### TabSchema

```python
class TabSchema(BaseModel):
    id: str
    name: str
    type: str  # 'datasource' or 'derived'
    parent_id: str | None = None
    datasource_id: str | None = None
    steps: list[PipelineStepSchema] = []
```

---

## Routes

### POST /api/v1/analysis

Create a new analysis.

**Request**:
```json
{
  "name": "Q4 Sales Analysis",
  "description": "Analyze Q4 sales trends",
  "datasource_ids": ["ds-uuid-1", "ds-uuid-2"],
  "pipeline_steps": [],
  "tabs": []
}
```

**Response** (200 OK):
```json
{
  "id": "analysis-uuid",
  "name": "Q4 Sales Analysis",
  "description": "Analyze Q4 sales trends",
  "pipeline_definition": {...},
  "status": "draft",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "result_path": null,
  "thumbnail": null,
  "tabs": [...]
}
```

**Errors**:
- 400: DataSource not found
- 500: Internal error

### GET /api/v1/analysis

List all analyses for gallery view.

**Response** (200 OK):
```json
[
  {
    "id": "analysis-uuid-1",
    "name": "Q4 Sales Analysis",
    "thumbnail": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "row_count": 10000,
    "column_count": 5
  },
  ...
]
```

### GET /api/v1/analysis/{analysis_id}

Get analysis details.

**Response** (200 OK):
```json
{
  "id": "analysis-uuid",
  "name": "Q4 Sales Analysis",
  "description": "...",
  "pipeline_definition": {
    "steps": [...],
    "datasource_ids": [...],
    "tabs": [...]
  },
  "status": "draft",
  ...
}
```

**Errors**:
- 404: Analysis not found

### PUT /api/v1/analysis/{analysis_id}

Update analysis.

**Request**:
```json
{
  "name": "Updated Name",
  "pipeline_steps": [...],
  "tabs": [...]
}
```

**Response** (200 OK): Updated analysis

**Errors**:
- 404: Analysis not found

### DELETE /api/v1/analysis/{analysis_id}

Delete analysis.

**Response** (200 OK):
```json
{
  "message": "Analysis deleted successfully"
}
```

**Errors**:
- 404: Analysis not found

### POST /api/v1/analysis/{analysis_id}/datasource/{datasource_id}

Link data source to analysis.

**Response** (200 OK):
```json
{
  "message": "DataSource linked successfully"
}
```

**Errors**:
- 404: Analysis or DataSource not found

### DELETE /api/v1/analysis/{analysis_id}/datasources/{datasource_id}

Unlink data source from analysis.

**Response** (204 No Content)

**Errors**:
- 404: Link not found

---

## Service Functions

### create_analysis

```python
async def create_analysis(
    session: AsyncSession,
    data: AnalysisCreateSchema
) -> AnalysisResponseSchema
```

**Logic**:
1. Validate all datasource IDs exist
2. Generate UUID for analysis
3. Create Analysis record
4. Create AnalysisDataSource junction records
5. Auto-generate tabs if not provided

### get_analysis

```python
async def get_analysis(
    session: AsyncSession,
    analysis_id: str
) -> AnalysisResponseSchema
```

**Logic**:
1. Query Analysis by ID
2. Raise ValueError if not found
3. Return response schema

### list_analyses

```python
async def list_analyses(
    session: AsyncSession
) -> list[AnalysisGalleryItemSchema]
```

**Logic**:
1. Query all analyses ordered by updated_at DESC
2. Map to gallery item schema

### update_analysis

```python
async def update_analysis(
    session: AsyncSession,
    analysis_id: str,
    data: AnalysisUpdateSchema
) -> AnalysisResponseSchema
```

**Logic**:
1. Get existing analysis
2. Update provided fields
3. Update `updated_at` timestamp
4. Update `pipeline_definition` if steps/tabs changed

### delete_analysis

```python
async def delete_analysis(
    session: AsyncSession,
    analysis_id: str
) -> dict
```

**Logic**:
1. Get existing analysis
2. Delete analysis (cascades to junction table)

### link_datasource

```python
async def link_datasource(
    session: AsyncSession,
    analysis_id: str,
    datasource_id: str
) -> dict
```

**Logic**:
1. Validate analysis exists
2. Validate datasource exists
3. Check if already linked
4. Create AnalysisDataSource record
5. Auto-create tab for new datasource

### unlink_datasource

```python
async def unlink_datasource(
    session: AsyncSession,
    analysis_id: str,
    datasource_id: str
) -> None
```

**Logic**:
1. Find junction record
2. Delete record
3. Remove associated tabs

---

## Pipeline Definition Structure

The `pipeline_definition` JSON stores the complete analysis configuration:

```json
{
  "steps": [
    {
      "id": "step-uuid-1",
      "type": "filter",
      "config": {
        "conditions": [
          {"column": "age", "operator": ">", "value": 18}
        ],
        "logic": "AND"
      },
      "depends_on": []
    },
    {
      "id": "step-uuid-2",
      "type": "select",
      "config": {
        "columns": ["name", "age", "city"]
      },
      "depends_on": ["step-uuid-1"]
    }
  ],
  "datasource_ids": ["ds-uuid-1"],
  "tabs": [
    {
      "id": "tab-uuid-1",
      "name": "Sales Data",
      "type": "datasource",
      "parent_id": null,
      "datasource_id": "ds-uuid-1",
      "steps": [/* same as above */]
    }
  ]
}
```

---

## Usage Examples

### Create Analysis

```python
# API call
POST /api/v1/analysis
{
    "name": "Customer Analysis",
    "datasource_ids": ["ds-123"]
}

# Service call
analysis = await create_analysis(session, AnalysisCreateSchema(
    name="Customer Analysis",
    datasource_ids=["ds-123"]
))
```

### Update Pipeline

```python
# API call
PUT /api/v1/analysis/analysis-123
{
    "pipeline_steps": [
        {
            "id": "step-1",
            "type": "filter",
            "config": {"conditions": [...], "logic": "AND"},
            "depends_on": []
        }
    ],
    "tabs": [...]
}
```

---

## See Also

- [DataSource Module](./datasource.md)
- [Compute Module](./compute.md)
- [Database Models](../database/models.md)
