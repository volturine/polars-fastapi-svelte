# Backend Modules

Documentation for all backend feature modules.

## Overview

The backend is organized into feature modules, each responsible for a specific domain:

| Module | Purpose | Routes |
|--------|---------|--------|
| [Analysis](./analysis.md) | Analysis CRUD, pipeline management | `/api/v1/analysis/*` |
| [DataSource](./datasource.md) | Data source management, file upload | `/api/v1/datasource/*` |
| [Compute](./compute.md) | Pipeline execution, engine lifecycle | `/api/v1/compute/*` |
| [Results](./results.md) | Result retrieval, pagination, export | `/api/v1/results/*` |
| [Health](./health.md) | Health checks | `/api/v1/health/*` |

## Module Structure

Each module follows a consistent layered structure:

```
module/
├── __init__.py      # Module exports
├── models.py        # SQLAlchemy ORM models
├── schemas.py       # Pydantic request/response schemas
├── routes.py        # FastAPI route handlers
└── service.py       # Business logic functions
```

### Layer Responsibilities

| Layer | File | Responsibility |
|-------|------|----------------|
| **Presentation** | `routes.py` | HTTP handling, request/response |
| **Contract** | `schemas.py` | Validation, serialization |
| **Business** | `service.py` | Logic, orchestration |
| **Data** | `models.py` | Database models, queries |

### Data Flow

```
HTTP Request
     │
     ▼
routes.py
├── Pydantic validation (schemas.py)
├── Dependency injection (session, manager)
└── Call service function
     │
     ▼
service.py
├── Business logic
├── Validation rules
└── Database operations
     │
     ▼
models.py
└── SQLAlchemy queries
     │
     ▼
Database
```

## Module Details

### Analysis Module

Manages analysis entities and their pipelines.

**Key Responsibilities**:
- Create, read, update, delete analyses
- Manage pipeline definitions (steps, tabs)
- Link/unlink data sources

**Key Files**:
- `models.py`: `Analysis`, `AnalysisDataSource`
- `schemas.py`: `AnalysisCreateSchema`, `AnalysisResponseSchema`, etc.
- `routes.py`: CRUD endpoints
- `service.py`: Business logic

[Full Documentation →](./analysis.md)

### DataSource Module

Manages data source connections and file uploads.

**Key Responsibilities**:
- Upload file-based data sources
- Connect to databases and APIs
- Extract and cache schema information

**Key Files**:
- `models.py`: `DataSource`
- `schemas.py`: `DataSourceCreate`, `DataSourceResponse`, `SchemaInfo`
- `routes.py`: Upload, connect, schema endpoints
- `service.py`: File handling, schema extraction

[Full Documentation →](./datasource.md)

### Compute Module

Handles pipeline execution and compute engine management.

**Key Responsibilities**:
- Execute analysis pipelines
- Manage compute engine lifecycle
- Track job status and results
- Preview step results

**Key Files**:
- `engine.py`: `PolarsComputeEngine` (subprocess)
- `manager.py`: `ProcessManager` (singleton)
- `step_converter.py`: Frontend → backend format conversion
- `schemas.py`: `ComputeStatusSchema`, `StepPreviewRequest`, etc.
- `routes.py`: Execute, status, preview endpoints
- `service.py`: Job tracking, execution coordination

[Full Documentation →](./compute.md)

### Results Module

Handles result retrieval, pagination, and export.

**Key Responsibilities**:
- Store results as Parquet files
- Provide paginated data access
- Export to multiple formats

**Key Files**:
- `schemas.py`: `ResultMetadataSchema`, `ResultDataSchema`
- `routes.py`: Metadata, data, export endpoints
- `service.py`: Parquet I/O, pagination, export

[Full Documentation →](./results.md)

### Health Module

Simple health check endpoint.

**Key Responsibilities**:
- Report application health status

**Key Files**:
- `routes.py`: Health check endpoint
- `service.py`: Status function

[Full Documentation →](./health.md)

## Common Patterns

### Error Handling

```python
@router.post('')
async def create(data: CreateSchema, session: AsyncSession = Depends(get_db)):
    try:
        return await service.create(session, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed: {str(e)}')
```

### Service Functions

```python
async def create(session: AsyncSession, data: CreateSchema) -> ResponseSchema:
    # Validate
    if not data.name:
        raise ValueError('Name is required')

    # Create
    entity = Model(id=str(uuid.uuid4()), name=data.name)
    session.add(entity)
    await session.commit()
    await session.refresh(entity)

    return ResponseSchema.model_validate(entity)
```

### Pydantic Schemas

```python
class CreateSchema(BaseModel):
    name: str
    description: str | None = None

class ResponseSchema(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

## Route Summary

| Method | Endpoint | Module | Description |
|--------|----------|--------|-------------|
| POST | `/api/v1/analysis` | Analysis | Create analysis |
| GET | `/api/v1/analysis` | Analysis | List analyses |
| GET | `/api/v1/analysis/{id}` | Analysis | Get analysis |
| PUT | `/api/v1/analysis/{id}` | Analysis | Update analysis |
| DELETE | `/api/v1/analysis/{id}` | Analysis | Delete analysis |
| POST | `/api/v1/datasource/upload` | DataSource | Upload file |
| POST | `/api/v1/datasource/connect` | DataSource | Connect DB/API |
| GET | `/api/v1/datasource` | DataSource | List data sources |
| GET | `/api/v1/datasource/{id}` | DataSource | Get data source |
| GET | `/api/v1/datasource/{id}/schema` | DataSource | Get schema |
| DELETE | `/api/v1/datasource/{id}` | DataSource | Delete data source |
| POST | `/api/v1/compute/execute` | Compute | Execute pipeline |
| POST | `/api/v1/compute/preview` | Compute | Preview step |
| GET | `/api/v1/compute/status/{id}` | Compute | Get job status |
| GET | `/api/v1/compute/result/{id}` | Compute | Get job result |
| POST | `/api/v1/compute/engine/spawn/{id}` | Compute | Spawn engine |
| POST | `/api/v1/compute/engine/keepalive/{id}` | Compute | Keepalive |
| GET | `/api/v1/results/{id}` | Results | Get metadata |
| GET | `/api/v1/results/{id}/data` | Results | Get data |
| POST | `/api/v1/results/{id}/export` | Results | Export |
| GET | `/api/v1/health` | Health | Health check |

## See Also

- [Analysis Module](./analysis.md)
- [DataSource Module](./datasource.md)
- [Compute Module](./compute.md)
- [Results Module](./results.md)
- [Health Module](./health.md)
