# Health Module

Documentation for the Health module, which provides health check endpoints.

## Overview

Simple health check endpoint for monitoring application status.

**Location**: `backend/modules/health/`

## Routes

### GET /api/v1/health

Returns application health status.

**Response** (200 OK):
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Service

```python
def get_health_status() -> dict:
    return {
        'status': 'ok',
        'version': settings.app_version
    }
```

## Usage

Health checks can be used for:
- Load balancer health probes
- Container orchestration readiness checks
- Monitoring systems
- Uptime verification
