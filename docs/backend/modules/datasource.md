# DataSource Module

Complete documentation for the DataSource module, which manages data source connections, file uploads, and schema extraction.

## Overview

The DataSource module handles all data source operations including file uploads, database connections, API connections, and schema extraction using Polars.

**Location**: `backend/modules/datasource/`

## Files

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy model: `DataSource` |
| `schemas.py` | Pydantic schemas for requests/responses |
| `routes.py` | FastAPI route handlers |
| `service.py` | Business logic and schema extraction |

---

## Models

### DataSource

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

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | String (PK) | UUID primary key |
| `name` | String | User-provided name |
| `source_type` | String | `file`, `database`, `api` |
| `config` | JSON | Source-specific configuration |
| `schema_cache` | JSON (nullable) | Cached schema information |
| `created_at` | DateTime | Creation timestamp |

---

## Source Type Configurations

### File Source

```json
{
  "source_type": "file",
  "config": {
    "file_path": "./data/uploads/uuid-123.csv",
    "file_type": "csv",
    "options": {}
  }
}
```

**Supported File Types**:
- `csv` - Comma-separated values
- `parquet` - Apache Parquet
- `json` - JSON (array of objects)
- `ndjson` / `jsonl` - Newline-delimited JSON
- `xlsx` - Excel spreadsheet

### Database Source

```json
{
  "source_type": "database",
  "config": {
    "connection_string": "postgresql://user:pass@host:5432/db",
    "query": "SELECT * FROM users WHERE active = true"
  }
}
```

**Supported Databases** (via SQLAlchemy/connectorx):
- PostgreSQL
- MySQL
- SQLite
- Others via connection string

### API Source

```json
{
  "source_type": "api",
  "config": {
    "url": "https://api.example.com/data",
    "method": "GET",
    "headers": {
      "Authorization": "Bearer token"
    },
    "auth": {
      "type": "bearer",
      "token": "..."
    }
  }
}
```

---

## Schemas

### DataSourceCreate

```python
class DataSourceCreate(BaseModel):
    name: str
    source_type: str  # 'file', 'database', 'api'
    config: dict
```

### DataSourceResponse

```python
class DataSourceResponse(BaseModel):
    id: str
    name: str
    source_type: str
    config: dict
    schema_cache: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### SchemaInfo

```python
class SchemaInfo(BaseModel):
    columns: list[ColumnSchema]
    row_count: int | None
```

### ColumnSchema

```python
class ColumnSchema(BaseModel):
    name: str
    dtype: str
    nullable: bool = True
```

---

## Routes

### POST /api/v1/datasource/upload

Upload a file-based data source.

**Request**: `multipart/form-data`
- `file`: File to upload
- `name`: Data source name

**Example with curl**:
```bash
curl -X POST http://localhost:8000/api/v1/datasource/upload \
  -F "file=@sales_data.csv" \
  -F "name=Sales Data"
```

**Response** (200 OK):
```json
{
  "id": "ds-uuid-123",
  "name": "Sales Data",
  "source_type": "file",
  "config": {
    "file_path": "./data/uploads/uuid-abc.csv",
    "file_type": "csv"
  },
  "schema_cache": {
    "columns": [
      {"name": "id", "dtype": "Int64", "nullable": true},
      {"name": "product", "dtype": "String", "nullable": true},
      {"name": "amount", "dtype": "Float64", "nullable": true}
    ],
    "row_count": 10000
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors**:
- 400: Unsupported file type
- 400: No filename provided
- 500: Upload failed

### POST /api/v1/datasource/connect

Connect to a database or API.

**Request**:
```json
{
  "name": "User Database",
  "source_type": "database",
  "config": {
    "connection_string": "postgresql://...",
    "query": "SELECT * FROM users"
  }
}
```

**Response** (200 OK): `DataSourceResponse`

### GET /api/v1/datasource

List all data sources.

**Response** (200 OK):
```json
[
  {
    "id": "ds-uuid-1",
    "name": "Sales Data",
    "source_type": "file",
    "config": {...},
    "schema_cache": {...},
    "created_at": "2024-01-15T10:30:00Z"
  },
  ...
]
```

### GET /api/v1/datasource/{datasource_id}

Get data source details.

**Response** (200 OK): `DataSourceResponse`

**Errors**:
- 404: DataSource not found

### GET /api/v1/datasource/{datasource_id}/schema

Get data source schema (extracts if not cached).

**Response** (200 OK):
```json
{
  "columns": [
    {"name": "id", "dtype": "Int64", "nullable": true},
    {"name": "name", "dtype": "String", "nullable": true},
    {"name": "age", "dtype": "Int64", "nullable": true}
  ],
  "row_count": 10000
}
```

**Errors**:
- 404: DataSource not found
- 400: Unsupported source type

### DELETE /api/v1/datasource/{datasource_id}

Delete data source.

**Response** (200 OK):
```json
{
  "message": "DataSource deleted successfully"
}
```

**Side Effects**:
- Deletes uploaded file (for file sources)
- Removes all AnalysisDataSource links (CASCADE)

---

## Service Functions

### create_file_datasource

```python
async def create_file_datasource(
    session: AsyncSession,
    name: str,
    file_path: str,
    file_type: str
) -> DataSource
```

Creates a file-based data source record.

### create_database_datasource

```python
async def create_database_datasource(
    session: AsyncSession,
    name: str,
    connection_string: str,
    query: str
) -> DataSource
```

Creates a database connection data source.

### create_api_datasource

```python
async def create_api_datasource(
    session: AsyncSession,
    name: str,
    url: str,
    method: str = 'GET',
    headers: dict | None = None,
    auth: dict | None = None
) -> DataSource
```

Creates an API connection data source.

### get_datasource_schema

```python
async def get_datasource_schema(
    session: AsyncSession,
    datasource_id: str
) -> SchemaInfo
```

Returns schema info, using cache if available.

**Logic**:
1. Get datasource from DB
2. Check `schema_cache` field
3. If cached, return cached schema
4. If not cached, call `_extract_schema`
5. Cache result in database
6. Return schema

### _extract_schema

```python
async def _extract_schema(datasource: DataSource) -> SchemaInfo
```

Extracts schema using Polars.

**For File Sources**:
```python
if file_type == 'csv':
    lf = pl.scan_csv(file_path)
elif file_type == 'parquet':
    lf = pl.scan_parquet(file_path)
elif file_type == 'json':
    lf = pl.scan_ndjson(file_path)
elif file_type == 'xlsx':
    lf = pl.read_excel(file_path).lazy()

schema = lf.collect_schema()
row_count = lf.select(pl.len()).collect().item()
```

**For Database Sources**:
```python
df = pl.read_database(query, connection_string)
schema = df.schema
row_count = len(df)
```

### get_datasource

```python
async def get_datasource(
    session: AsyncSession,
    datasource_id: str
) -> DataSource | None
```

Returns datasource or None.

### list_datasources

```python
async def list_datasources(
    session: AsyncSession
) -> list[DataSource]
```

Returns all datasources ordered by created_at DESC.

### delete_datasource

```python
async def delete_datasource(
    session: AsyncSession,
    datasource_id: str
) -> dict
```

Deletes datasource and associated file.

---

## Schema Extraction Details

### Polars Data Types

Schema extraction maps Polars dtypes:

| Polars Type | Schema String |
|-------------|---------------|
| `pl.Int8` | `"Int8"` |
| `pl.Int16` | `"Int16"` |
| `pl.Int32` | `"Int32"` |
| `pl.Int64` | `"Int64"` |
| `pl.Float32` | `"Float32"` |
| `pl.Float64` | `"Float64"` |
| `pl.String` | `"String"` |
| `pl.Boolean` | `"Boolean"` |
| `pl.Date` | `"Date"` |
| `pl.Datetime` | `"Datetime"` |
| `pl.Duration` | `"Duration"` |
| `pl.List` | `"List"` |
| `pl.Null` | `"Null"` |

### Lazy Evaluation

Schema extraction uses lazy evaluation where possible:

```python
# Lazy - no data loaded
lf = pl.scan_csv(file_path)

# Get schema without loading data
schema = lf.collect_schema()  # Returns dict

# Count rows with streaming
row_count = lf.select(pl.len()).collect().item()
```

This is memory-efficient for large files.

### Caching

Schema is cached in the `schema_cache` field:

```python
# Check cache
if datasource.schema_cache:
    return SchemaInfo.model_validate(datasource.schema_cache)

# Extract and cache
schema_info = await _extract_schema(datasource)
datasource.schema_cache = schema_info.model_dump()
await session.commit()
```

---

## File Upload Handling

### Upload Process

1. **Validate extension**:
   ```python
   ALLOWED_EXTENSIONS = {'.csv', '.parquet', '.json', '.ndjson', '.xlsx'}
   ext = Path(filename).suffix.lower()
   if ext not in ALLOWED_EXTENSIONS:
       raise HTTPException(400, f'Unsupported file type: {ext}')
   ```

2. **Generate unique filename**:
   ```python
   unique_name = f'{uuid.uuid4()}{ext}'
   file_path = settings.upload_dir / unique_name
   ```

3. **Write file**:
   ```python
   contents = await file.read()
   with open(file_path, 'wb') as f:
       f.write(contents)
   ```

4. **Create record**:
   ```python
   datasource = await create_file_datasource(
       session, name, str(file_path), ext[1:]  # Remove leading dot
   )
   ```

### File Size Limit

```python
# config.py
max_upload_size: int = 10 * 1024 * 1024 * 1024  # 10GB
```

---

## Usage Examples

### Upload File

```bash
curl -X POST http://localhost:8000/api/v1/datasource/upload \
  -F "file=@data.csv" \
  -F "name=My Data"
```

### Connect Database

```bash
curl -X POST http://localhost:8000/api/v1/datasource/connect \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production DB",
    "source_type": "database",
    "config": {
      "connection_string": "postgresql://...",
      "query": "SELECT * FROM orders"
    }
  }'
```

### Get Schema

```bash
curl http://localhost:8000/api/v1/datasource/ds-123/schema
```

---

## See Also

- [Analysis Module](./analysis.md)
- [Compute Module](./compute.md)
- [Database Models](../database/models.md)
