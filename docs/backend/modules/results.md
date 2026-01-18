# Results Module

Documentation for the Results module, which handles result storage, retrieval, pagination, and export.

## Overview

The Results module provides access to computed analysis results stored as Parquet files.

**Location**: `backend/modules/results/`

## Files

| File | Purpose |
|------|---------|
| `schemas.py` | Pydantic schemas |
| `routes.py` | FastAPI route handlers |
| `service.py` | Result I/O and export |

---

## Schemas

### ResultMetadataSchema

```python
class ResultMetadataSchema(BaseModel):
    analysis_id: str
    row_count: int
    column_count: int
    columns_schema: list[ColumnSchema]
    created_at: datetime
```

### ResultDataSchema

```python
class ResultDataSchema(BaseModel):
    columns: list[str]
    data: list[dict]
    total_count: int
    page: int
    page_size: int
```

### ExportRequestSchema

```python
class ExportRequestSchema(BaseModel):
    format: str  # csv, parquet, excel, json
```

---

## Routes

### GET /api/v1/results/{analysis_id}

Get result metadata.

**Response** (200 OK):
```json
{
  "analysis_id": "analysis-uuid",
  "row_count": 10000,
  "column_count": 5,
  "columns_schema": [
    {"name": "id", "dtype": "Int64", "nullable": true},
    {"name": "name", "dtype": "String", "nullable": true}
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /api/v1/results/{analysis_id}/data

Get paginated result data.

**Query Parameters**:
- `page`: Page number (default: 1, min: 1)
- `page_size`: Rows per page (default: 100, max: 1000)

**Response** (200 OK):
```json
{
  "columns": ["id", "name", "age"],
  "data": [
    {"id": 1, "name": "Alice", "age": 30},
    {"id": 2, "name": "Bob", "age": 25}
  ],
  "total_count": 10000,
  "page": 1,
  "page_size": 100
}
```

### POST /api/v1/results/{analysis_id}/export

Export result to file.

**Request**:
```json
{
  "format": "csv"
}
```

**Response**: File download

**Supported Formats**:
- `csv` - Comma-separated values
- `parquet` - Apache Parquet
- `excel` - Excel (.xlsx)
- `json` - JSON array

### DELETE /api/v1/results/{analysis_id}

Delete result file.

**Response** (200 OK):
```json
{
  "message": "Result deleted successfully"
}
```

---

## Service Functions

### store_result

```python
async def store_result(analysis_id: str, df: pl.DataFrame) -> str
```

Stores DataFrame as Parquet.

```python
result_path = f'{settings.results_dir}/{analysis_id}.parquet'
df.write_parquet(result_path)
return result_path
```

### get_result_metadata

```python
async def get_result_metadata(analysis_id: str) -> ResultMetadataSchema
```

Reads Parquet metadata without loading data.

### get_result_data

```python
async def get_result_data(
    analysis_id: str,
    page: int = 1,
    page_size: int = 100
) -> ResultDataSchema
```

Returns paginated data.

```python
df = pl.scan_parquet(result_path)
offset = (page - 1) * page_size
data = df.slice(offset, page_size).collect()
```

### export_result

```python
async def export_result(
    analysis_id: str,
    format: str
) -> str
```

Exports to specified format, returns file path.

---

## Storage

Results are stored as Parquet files:

```
./data/results/
├── analysis-uuid-1.parquet
├── analysis-uuid-2.parquet
└── ...
```

**Why Parquet?**
- Columnar format (efficient for analytics)
- Compressed storage
- Schema preservation
- Fast partial reads (pagination)

---

## See Also

- [Compute Module](./compute.md)
- [Analysis Module](./analysis.md)
