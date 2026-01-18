# Creating Datasources

Guide to adding and configuring data sources.

## Overview

Datasources define where data comes from. The platform supports:

- **File uploads**: CSV, Parquet, JSON, Excel
- **Database connections**: PostgreSQL, MySQL, SQLite
- **API endpoints**: REST APIs (planned)

## File Datasources

### Uploading Files via UI

1. Navigate to **Data Sources** in the sidebar
2. Click **Add Data Source**
3. Select the **File Upload** tab
4. Choose your file (CSV, Parquet, JSON, or Excel)
5. Enter a name for the datasource
6. Click **Upload**

### Supported File Types

| Type | Extension | Read Method | Notes |
|------|-----------|-------------|-------|
| CSV | `.csv` | `pl.scan_csv()` | Lazy loading |
| Parquet | `.parquet` | `pl.scan_parquet()` | Lazy loading, preserves types |
| JSON | `.json`, `.ndjson` | `pl.scan_ndjson()` | Newline-delimited JSON |
| Excel | `.xlsx`, `.xls` | `pl.read_excel()` | Loaded eagerly |

### File Size Limits

Default maximum: **10GB** (configurable via `MAX_UPLOAD_SIZE`)

### Via API

```bash
curl -X POST "http://localhost:8000/api/v1/datasources/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/data.csv" \
  -F "name=My Dataset"
```

### Via Python

```python
from modules.datasource.service import create_file_datasource

datasource = await create_file_datasource(
    session,
    name="Sales Data",
    file_path="/data/uploads/sales.csv",
    file_type="csv",
    options={}
)
```

## Database Datasources

### Configuration

Database datasources require:
- **Connection string**: Database URL
- **Query**: SQL query to execute

### Connection String Format

```
driver://username:password@host:port/database
```

#### PostgreSQL

```
postgresql://user:password@localhost:5432/mydb
```

#### MySQL

```
mysql://user:password@localhost:3306/mydb
```

#### SQLite

```
sqlite:///path/to/database.db
```

### Creating via API

```bash
curl -X POST "http://localhost:8000/api/v1/datasources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Database",
    "source_type": "database",
    "config": {
      "connection_string": "postgresql://user:pass@localhost:5432/sales",
      "query": "SELECT * FROM transactions WHERE date > '\''2024-01-01'\''"
    }
  }'
```

### Via Python

```python
from modules.datasource.service import create_database_datasource

datasource = await create_database_datasource(
    session,
    name="Sales Database",
    connection_string="postgresql://user:pass@localhost:5432/sales",
    query="SELECT * FROM transactions WHERE date > '2024-01-01'"
)
```

### Query Best Practices

1. **Filter in query**: Reduce data before loading
   ```sql
   SELECT * FROM orders WHERE status = 'completed'
   ```

2. **Select needed columns**: Don't use `SELECT *` for large tables
   ```sql
   SELECT id, amount, date FROM orders
   ```

3. **Use indexed columns**: Filter on indexed columns for speed

4. **Test queries first**: Verify query works before creating datasource

## API Datasources (Planned)

API datasources will fetch data from REST endpoints.

### Configuration Schema

```typescript
interface APIDataSourceConfig {
    url: string;           // API endpoint URL
    method?: string;       // HTTP method (default: GET)
    headers?: Record<string, string>;  // Request headers
    auth?: {
        type: 'basic' | 'bearer' | 'api_key';
        // ... auth details
    };
}
```

### Future Example

```json
{
    "name": "Weather API",
    "source_type": "api",
    "config": {
        "url": "https://api.weather.com/data",
        "method": "GET",
        "headers": {
            "Accept": "application/json"
        },
        "auth": {
            "type": "api_key",
            "header": "X-API-Key",
            "key": "your-api-key"
        }
    }
}
```

## Schema Detection

When a datasource is created, the system automatically detects the schema:

### Schema Information

```typescript
interface SchemaInfo {
    columns: ColumnSchema[];
    row_count: number | null;
}

interface ColumnSchema {
    name: string;      // Column name
    dtype: string;     // Polars data type
    nullable: boolean; // Can contain nulls
}
```

### Fetching Schema

```bash
curl "http://localhost:8000/api/v1/datasources/{id}/schema"
```

Response:
```json
{
    "columns": [
        {"name": "id", "dtype": "Int64", "nullable": false},
        {"name": "name", "dtype": "String", "nullable": true},
        {"name": "amount", "dtype": "Float64", "nullable": false}
    ],
    "row_count": 10000
}
```

### Schema Caching

Schema is cached after first extraction to avoid repeated reads. Cache is stored in `schema_cache` field.

## Managing Datasources

### List All Datasources

```bash
curl "http://localhost:8000/api/v1/datasources"
```

### Get Single Datasource

```bash
curl "http://localhost:8000/api/v1/datasources/{id}"
```

### Delete Datasource

```bash
curl -X DELETE "http://localhost:8000/api/v1/datasources/{id}"
```

**Note**: Deleting a file datasource also removes the uploaded file.

## TypeScript API Client

### Using the Frontend Client

```typescript
import { createDatasource, getDatasources } from '$lib/api/datasource';

// List all datasources
const result = await getDatasources();
if (result.isOk()) {
    const datasources = result.value;
}

// Create file datasource (after upload)
const result = await createDatasource({
    name: 'My Data',
    source_type: 'file',
    config: {
        file_path: '/uploads/data.csv',
        file_type: 'csv'
    }
});
```

### File Upload

```typescript
async function uploadFile(file: File, name: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);

    const response = await fetch('/api/v1/datasources/upload', {
        method: 'POST',
        body: formData
    });

    return response.json();
}
```

## Polars Data Types

Common data types detected:

| Polars Type | Description | Python Equivalent |
|-------------|-------------|-------------------|
| `Int64` | 64-bit integer | `int` |
| `Float64` | 64-bit float | `float` |
| `String` | UTF-8 string | `str` |
| `Boolean` | True/False | `bool` |
| `Date` | Date without time | `datetime.date` |
| `Datetime` | Date with time | `datetime.datetime` |
| `Duration` | Time duration | `datetime.timedelta` |
| `List` | Array/list column | `list` |
| `Struct` | Nested structure | `dict` |

## Troubleshooting

### File Upload Errors

**"File too large"**
- Check `MAX_UPLOAD_SIZE` setting
- Consider compressing to Parquet format

**"Unsupported file type"**
- Verify file extension matches content
- Supported: `.csv`, `.parquet`, `.json`, `.ndjson`, `.xlsx`, `.xls`

### Database Connection Errors

**"Connection refused"**
- Verify database is running
- Check host and port
- Verify network connectivity

**"Authentication failed"**
- Check username and password
- Verify user has required permissions

**"Query error"**
- Test query in database client first
- Check table and column names

### Schema Detection Issues

**"Schema extraction not supported"**
- API datasources don't support schema detection yet
- Ensure file exists and is readable

**"Null row_count"**
- Schema cache may need refresh
- Delete and re-create datasource

## Best Practices

1. **Use Parquet for large data**: Better compression, preserves types
2. **Name descriptively**: Include date or version in name
3. **Filter at source**: Use SQL WHERE clauses for database sources
4. **Test before creating analysis**: Verify schema looks correct
5. **Clean up unused datasources**: Delete to free disk space

## See Also

- [Building Pipelines](./building-pipelines.md) - Using datasources in pipelines
- [Reference: Configuration](../reference/configuration.md) - Environment settings
- [Backend: Datasource Module](../backend/modules/datasource.md) - Module documentation
