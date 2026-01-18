# API Endpoints

Complete reference for all REST API endpoints.

## Analysis Endpoints

### List Analyses

```
GET /api/v1/analysis
```

Returns all analyses as gallery items.

**Response** `200 OK`:
```json
[
    {
        "id": "abc-123",
        "name": "Sales Analysis",
        "thumbnail": null,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T11:45:00Z",
        "row_count": 1000,
        "column_count": 5
    }
]
```

---

### Create Analysis

```
POST /api/v1/analysis
```

Create a new analysis with pipeline definition.

**Request Body**:
```json
{
    "name": "My Analysis",
    "description": "Optional description",
    "datasource_ids": ["ds-uuid-1"],
    "pipeline_steps": [],
    "tabs": [
        {
            "id": "tab-1",
            "name": "Source 1",
            "type": "datasource",
            "parent_id": null,
            "datasource_id": "ds-uuid-1",
            "steps": []
        }
    ]
}
```

**Response** `200 OK`:
```json
{
    "id": "analysis-uuid",
    "name": "My Analysis",
    "description": "Optional description",
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
- `400`: Invalid datasource ID
- `500`: Server error

---

### Get Analysis

```
GET /api/v1/analysis/{analysis_id}
```

Get a specific analysis by ID.

**Parameters**:
- `analysis_id` (path): Analysis UUID

**Response** `200 OK`:
```json
{
    "id": "analysis-uuid",
    "name": "My Analysis",
    "description": "Optional description",
    "pipeline_definition": {
        "steps": [...],
        "datasource_ids": [...],
        "tabs": [...]
    },
    "status": "draft",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "result_path": null,
    "thumbnail": null,
    "tabs": [...]
}
```

**Errors**:
- `404`: Analysis not found

---

### Update Analysis

```
PUT /api/v1/analysis/{analysis_id}
```

Update an existing analysis.

**Parameters**:
- `analysis_id` (path): Analysis UUID

**Request Body** (all fields optional):
```json
{
    "name": "Updated Name",
    "description": "Updated description",
    "pipeline_steps": [...],
    "status": "completed",
    "tabs": [...]
}
```

**Response** `200 OK`: Updated analysis object

**Errors**:
- `404`: Analysis not found

---

### Delete Analysis

```
DELETE /api/v1/analysis/{analysis_id}
```

Delete an analysis and its associations.

**Parameters**:
- `analysis_id` (path): Analysis UUID

**Response** `200 OK`:
```json
{
    "message": "Analysis {id} deleted successfully"
}
```

**Errors**:
- `404`: Analysis not found

---

### Link Datasource

```
POST /api/v1/analysis/{analysis_id}/datasource/{datasource_id}
```

Link a datasource to an analysis.

**Parameters**:
- `analysis_id` (path): Analysis UUID
- `datasource_id` (path): Datasource UUID

**Response** `200 OK`:
```json
{
    "message": "DataSource {ds_id} linked to Analysis {analysis_id}"
}
```

---

### Unlink Datasource

```
DELETE /api/v1/analysis/{analysis_id}/datasources/{datasource_id}
```

Unlink a datasource from an analysis.

**Response** `204 No Content`

---

## DataSource Endpoints

### List Datasources

```
GET /api/v1/datasource
```

Returns all datasources.

**Response** `200 OK`:
```json
[
    {
        "id": "ds-uuid",
        "name": "Sales Data",
        "source_type": "file",
        "config": {
            "file_path": "./data/uploads/sales.csv",
            "file_type": "csv"
        },
        "created_at": "2024-01-15T10:30:00Z"
    }
]
```

---

### Upload File

```
POST /api/v1/datasource/upload
Content-Type: multipart/form-data
```

Upload a file as a new datasource.

**Form Data**:
- `file`: File to upload
- `name`: Datasource name

**Response** `200 OK`:
```json
{
    "id": "ds-uuid",
    "name": "My Data",
    "source_type": "file",
    "config": {
        "file_path": "./data/uploads/uuid.csv",
        "file_type": "csv"
    },
    "schema_cache": {
        "columns": [
            {"name": "id", "dtype": "Int64", "nullable": false},
            {"name": "name", "dtype": "String", "nullable": true}
        ],
        "row_count": 1000
    },
    "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Connect Database

```
POST /api/v1/datasource/database
```

Connect to a database as a datasource.

**Request Body**:
```json
{
    "name": "Users DB",
    "connection_string": "postgresql://user:pass@localhost/db",
    "query": "SELECT * FROM users"
}
```

**Response** `200 OK`: Datasource object

---

### Connect API

```
POST /api/v1/datasource/api
```

Connect to an API as a datasource.

**Request Body**:
```json
{
    "name": "External API",
    "url": "https://api.example.com/data",
    "method": "GET",
    "headers": {}
}
```

**Response** `200 OK`: Datasource object

---

### Get Datasource

```
GET /api/v1/datasource/{datasource_id}
```

Get a specific datasource.

**Response** `200 OK`: Datasource object

---

### Get Schema

```
GET /api/v1/datasource/{datasource_id}/schema
```

Get the schema of a datasource.

**Response** `200 OK`:
```json
{
    "columns": [
        {"name": "id", "dtype": "Int64", "nullable": false},
        {"name": "name", "dtype": "String", "nullable": true},
        {"name": "amount", "dtype": "Float64", "nullable": true}
    ],
    "row_count": 10000
}
```

---

### Preview Data

```
GET /api/v1/datasource/{datasource_id}/preview?rows=100
```

Preview datasource data.

**Query Parameters**:
- `rows` (optional): Number of rows (default: 100, max: 1000)

**Response** `200 OK`:
```json
{
    "schema": {...},
    "data": [
        {"id": 1, "name": "Alice", "amount": 100.50},
        {"id": 2, "name": "Bob", "amount": 200.75}
    ],
    "total_rows": 10000
}
```

---

### Delete Datasource

```
DELETE /api/v1/datasource/{datasource_id}
```

Delete a datasource.

**Response** `204 No Content`

---

## Compute Endpoints

### Execute Pipeline

```
POST /api/v1/compute/execute
```

Execute a pipeline for an analysis tab.

**Request Body**:
```json
{
    "analysis_id": "analysis-uuid",
    "tab_id": "tab-uuid"
}
```

**Response** `200 OK`:
```json
{
    "job_id": "job-uuid"
}
```

---

### Get Job Status

```
GET /api/v1/compute/job/{job_id}
```

Get the status of a compute job.

**Response** `200 OK`:
```json
{
    "job_id": "job-uuid",
    "status": "running",
    "progress": 0.5,
    "current_step": "Applying filter",
    "error": null
}
```

**Status Values**:
- `pending`: Job queued
- `running`: Job executing
- `completed`: Job finished successfully
- `failed`: Job failed

---

### Get Job Result

```
GET /api/v1/compute/job/{job_id}/result
```

Get the result of a completed job.

**Response** `200 OK`:
```json
{
    "schema": {
        "id": "Int64",
        "name": "String",
        "total": "Float64"
    },
    "row_count": 500,
    "sample_data": [
        {"id": 1, "name": "Category A", "total": 1500.00},
        {"id": 2, "name": "Category B", "total": 2300.00}
    ]
}
```

---

### Engine Status

```
GET /api/v1/compute/engine/{analysis_id}/status
```

Get compute engine status for an analysis.

**Response** `200 OK`:
```json
{
    "analysis_id": "analysis-uuid",
    "status": "idle",
    "process_id": 12345,
    "last_activity": "2024-01-15T10:30:00Z"
}
```

---

### Keepalive

```
POST /api/v1/compute/engine/{analysis_id}/keepalive
```

Keep the compute engine alive (prevent idle timeout).

**Response** `200 OK`:
```json
{
    "message": "Engine keepalive successful"
}
```

---

### Shutdown Engine

```
DELETE /api/v1/compute/engine/{analysis_id}
```

Manually shutdown a compute engine.

**Response** `200 OK`:
```json
{
    "message": "Engine shutdown successful"
}
```

---

## Results Endpoints

### Get Results

```
GET /api/v1/results/{analysis_id}?page=1&page_size=100
```

Get paginated results for an analysis.

**Query Parameters**:
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Rows per page (default: 100, max: 10000)

**Response** `200 OK`:
```json
{
    "data": [...],
    "total_rows": 5000,
    "page": 1,
    "page_size": 100,
    "total_pages": 50
}
```

---

### Get Result Schema

```
GET /api/v1/results/{analysis_id}/schema
```

Get the schema of stored results.

**Response** `200 OK`:
```json
{
    "columns": [
        {"name": "id", "dtype": "Int64"},
        {"name": "category", "dtype": "String"},
        {"name": "total", "dtype": "Float64"}
    ]
}
```

---

### Download Results

```
GET /api/v1/results/{analysis_id}/download?format=csv
```

Export results as a file.

**Query Parameters**:
- `format`: Export format (`csv`, `parquet`, `json`)

**Response**: File download

---

## Health Endpoint

### Health Check

```
GET /api/v1/health
```

Check API health status.

**Response** `200 OK`:
```json
{
    "status": "ok",
    "version": "1.0.0"
}
```

---

## See Also

- [Schemas](../schemas/README.md) - Request/response schemas
- [API Overview](../README.md) - API documentation index
