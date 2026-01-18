# API Schemas

Pydantic schema definitions for API requests and responses.

## Overview

All schemas use Pydantic V2 with `model_config = ConfigDict(from_attributes=True)` for ORM compatibility.

---

## Analysis Schemas

### PipelineStepSchema

Individual pipeline step.

```python
class PipelineStepSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    config: dict
    depends_on: list[str] = []
```

**Example**:
```json
{
    "id": "step-uuid",
    "type": "filter",
    "config": {
        "conditions": [{"column": "age", "operator": ">", "value": 18}],
        "logic": "AND"
    },
    "depends_on": ["previous-step-id"]
}
```

### TabSchema

Analysis tab definition.

```python
class TabSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    parent_id: str | None = None
    datasource_id: str | None = None
    steps: list[PipelineStepSchema] = []
```

**Example**:
```json
{
    "id": "tab-ds-123",
    "name": "Sales Data",
    "type": "datasource",
    "parent_id": null,
    "datasource_id": "ds-123",
    "steps": []
}
```

### AnalysisCreateSchema

Request schema for creating an analysis.

```python
class AnalysisCreateSchema(BaseModel):
    name: str
    description: str | None = None
    datasource_ids: list[str]
    pipeline_steps: list[PipelineStepSchema]
    tabs: list[TabSchema] = []
```

### AnalysisUpdateSchema

Request schema for updating an analysis.

```python
class AnalysisUpdateSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    pipeline_steps: list[PipelineStepSchema] | None = None
    status: str | None = None
    tabs: list[TabSchema] | None = None
```

### AnalysisResponseSchema

Response schema for analysis.

```python
class AnalysisResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    pipeline_definition: dict
    status: str
    created_at: datetime
    updated_at: datetime
    result_path: str | None
    thumbnail: str | None
    tabs: list[TabSchema] = []
```

### AnalysisGalleryItemSchema

Compact schema for gallery listing.

```python
class AnalysisGalleryItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    thumbnail: str | None
    created_at: datetime
    updated_at: datetime
    row_count: int | None = None
    column_count: int | None = None
```

---

## DataSource Schemas

### DataSourceConfigFile

File datasource configuration.

```python
class DataSourceConfigFile(BaseModel):
    file_path: str
    file_type: str  # csv, parquet, json, excel
    options: dict = {}
```

### DataSourceConfigDatabase

Database datasource configuration.

```python
class DataSourceConfigDatabase(BaseModel):
    connection_string: str
    query: str
```

### DataSourceConfigApi

API datasource configuration.

```python
class DataSourceConfigApi(BaseModel):
    url: str
    method: str = "GET"
    headers: dict = {}
    auth: dict = {}
```

### SchemaColumnInfo

Column information.

```python
class SchemaColumnInfo(BaseModel):
    name: str
    dtype: str
    nullable: bool = True
```

### SchemaInfo

Schema information.

```python
class SchemaInfo(BaseModel):
    columns: list[SchemaColumnInfo]
    row_count: int | None = None
```

### DataSourceResponseSchema

Response schema for datasource.

```python
class DataSourceResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    source_type: str  # file, database, api
    config: dict
    schema_cache: SchemaInfo | None = None
    created_at: datetime
```

### FileUploadRequest

File upload form data.

```python
# Uses FastAPI Form and File
file: UploadFile
name: str
```

### DatabaseConnectRequest

Database connection request.

```python
class DatabaseConnectRequest(BaseModel):
    name: str
    connection_string: str
    query: str
```

### ApiConnectRequest

API connection request.

```python
class ApiConnectRequest(BaseModel):
    name: str
    url: str
    method: str = "GET"
    headers: dict = {}
```

---

## Compute Schemas

### ExecuteRequest

Pipeline execution request.

```python
class ExecuteRequest(BaseModel):
    analysis_id: str
    tab_id: str
```

### JobStatus

Enum for job status.

```python
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

### JobStatusResponse

Job status response.

```python
class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float  # 0.0 to 1.0
    current_step: str | None = None
    error: str | None = None
```

### JobResultResponse

Job result response.

```python
class JobResultResponse(BaseModel):
    schema: dict[str, str]  # column: dtype
    row_count: int
    sample_data: list[dict]  # Up to 5000 rows
```

### EngineStatus

Enum for engine status.

```python
class EngineStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    TERMINATED = "terminated"
```

### EngineStatusResponse

Engine status response.

```python
class EngineStatusResponse(BaseModel):
    analysis_id: str
    status: EngineStatus
    process_id: int | None = None
    last_activity: str | None = None
```

---

## Results Schemas

### PaginatedResultsResponse

Paginated results response.

```python
class PaginatedResultsResponse(BaseModel):
    data: list[dict]
    total_rows: int
    page: int
    page_size: int
    total_pages: int
```

### ResultSchemaResponse

Result schema response.

```python
class ResultSchemaResponse(BaseModel):
    columns: list[dict]  # name, dtype
```

---

## Health Schemas

### HealthResponse

Health check response.

```python
class HealthResponse(BaseModel):
    status: str
    version: str
```

---

## Common Patterns

### Nullable Fields

```python
# Optional field with default None
description: str | None = None

# Required field that can be None
result_path: str | None
```

### DateTime Handling

```python
from datetime import datetime

created_at: datetime  # ISO 8601 format in JSON
```

### ORM Mode

```python
model_config = ConfigDict(from_attributes=True)
```

Enables creating schema from SQLAlchemy model:

```python
# In service
analysis = await session.execute(...)
return AnalysisResponseSchema.model_validate(analysis)
```

### Nested Schemas

```python
class ParentSchema(BaseModel):
    items: list[ChildSchema] = []
```

---

## Validation Examples

### Custom Validator

```python
from pydantic import field_validator

class MySchema(BaseModel):
    email: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('Invalid email')
        return v
```

### Constrained Types

```python
from pydantic import conint, constr

class MySchema(BaseModel):
    page: conint(ge=1) = 1           # >= 1
    page_size: conint(ge=1, le=1000) = 100  # 1-1000
    name: constr(min_length=1)       # Non-empty string
```

---

## See Also

- [Endpoints](../endpoints/README.md) - API endpoint reference
- [Backend Modules](../../backend/modules/README.md) - Implementation details
