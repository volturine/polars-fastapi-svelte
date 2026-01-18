# API Documentation

Complete REST API documentation for the Polars-FastAPI-Svelte Analysis Platform.

## Overview

The backend exposes a REST API at `/api/v1/` with JSON request/response bodies.

## Base URL

| Environment | URL |
|-------------|-----|
| Development | `http://localhost:8000/api/v1` |
| Production | `http://<host>:8000/api/v1` |

## Contents

| Document | Description |
|----------|-------------|
| [Endpoints](./endpoints/README.md) | API endpoint reference |
| [Schemas](./schemas/README.md) | Request/response schemas |

## Authentication

Currently, the API does not require authentication (local-first design).

## Common Headers

```
Content-Type: application/json
Accept: application/json
```

## Response Format

### Success Response

```json
{
    "id": "uuid",
    "name": "Example",
    "created_at": "2024-01-15T10:30:00Z"
}
```

### Error Response

```json
{
    "detail": "Error message describing what went wrong"
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (delete success) |
| 400 | Bad Request (validation error) |
| 404 | Not Found |
| 500 | Internal Server Error |

## Endpoint Summary

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analysis` | List all analyses |
| POST | `/analysis` | Create analysis |
| GET | `/analysis/{id}` | Get analysis |
| PUT | `/analysis/{id}` | Update analysis |
| DELETE | `/analysis/{id}` | Delete analysis |
| POST | `/analysis/{id}/datasource/{ds_id}` | Link datasource |
| DELETE | `/analysis/{id}/datasources/{ds_id}` | Unlink datasource |

### DataSource

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/datasource` | List all datasources |
| POST | `/datasource/upload` | Upload file |
| POST | `/datasource/database` | Connect database |
| POST | `/datasource/api` | Connect API |
| GET | `/datasource/{id}` | Get datasource |
| GET | `/datasource/{id}/schema` | Get schema |
| GET | `/datasource/{id}/preview` | Preview data |
| DELETE | `/datasource/{id}` | Delete datasource |

### Compute

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/compute/execute` | Execute pipeline |
| GET | `/compute/job/{id}` | Get job status |
| GET | `/compute/job/{id}/result` | Get job result |
| DELETE | `/compute/engine/{analysis_id}` | Shutdown engine |
| GET | `/compute/engine/{analysis_id}/status` | Engine status |
| POST | `/compute/engine/{analysis_id}/keepalive` | Keep engine alive |

### Results

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/results/{analysis_id}` | Get paginated results |
| GET | `/results/{analysis_id}/schema` | Get result schema |
| GET | `/results/{analysis_id}/download` | Export results |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

## OpenAPI Documentation

Interactive API documentation available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Rate Limiting

No rate limiting is enforced (local-first application).

## CORS

CORS is configured to allow:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- Custom origins via `CORS_ORIGINS` env var

## See Also

- [Endpoints](./endpoints/README.md) - Detailed endpoint docs
- [Schemas](./schemas/README.md) - Request/response schemas
- [Backend Modules](../backend/modules/README.md) - Implementation details
