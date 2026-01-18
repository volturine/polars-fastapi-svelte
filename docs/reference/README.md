# Reference Documentation

Technical reference for the Polars-FastAPI-Svelte Analysis Platform.

## Contents

| Document | Description |
|----------|-------------|
| [Configuration](./configuration.md) | Environment variables and settings |
| [Polars Operations](./polars-operations.md) | Complete operation reference |
| [Type Definitions](./type-definitions.md) | TypeScript type reference |

## Quick Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./database/app.db` | Database connection |
| `DEBUG` | `false` | Enable debug logging |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Allowed CORS origins |
| `COMPUTE_TIMEOUT` | `300` | Pipeline execution timeout (seconds) |
| `JOB_TTL` | `3600` | Job result retention (seconds) |
| `MAX_UPLOAD_SIZE` | `10GB` | Maximum file upload size |

### Supported File Types

| Type | Extension | Read Method |
|------|-----------|-------------|
| CSV | `.csv` | `pl.scan_csv()` |
| Parquet | `.parquet` | `pl.scan_parquet()` |
| JSON (NDJSON) | `.json`, `.ndjson` | `pl.scan_ndjson()` |
| Excel | `.xlsx`, `.xls` | `pl.read_excel()` |

### Polars Data Types

| Type | Description |
|------|-------------|
| `Int8`, `Int16`, `Int32`, `Int64` | Signed integers |
| `UInt8`, `UInt16`, `UInt32`, `UInt64` | Unsigned integers |
| `Float32`, `Float64` | Floating point |
| `String`, `Utf8` | Text |
| `Boolean` | True/False |
| `Date` | Date (no time) |
| `Datetime` | Date with time |
| `Duration` | Time duration |
| `List` | List/array column |
| `Struct` | Nested structure |
| `Null` | Null type |

### API Base URLs

| Environment | URL |
|-------------|-----|
| Development | `http://localhost:8000/api/v1` |
| Frontend Dev | Proxied via Vite |

### Ports

| Service | Port |
|---------|------|
| Backend API | 8000 |
| Frontend Dev | 3000 |
| Frontend Preview | 4173 |

## See Also

- [Backend Documentation](../backend/README.md)
- [Frontend Documentation](../frontend/README.md)
- [API Documentation](../api/README.md)
