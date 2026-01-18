# FastAPI Application

Detailed documentation of the FastAPI application setup, lifecycle, and configuration.

## Entry Point

**File**: `backend/main.py`

The application entry point creates and configures the FastAPI application:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import router
from core.config import settings
from core.database import init_db
from modules.compute.manager import get_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    logger.info('Starting application...')
    await init_db()
    yield
    # Shutdown
    logger.info('Shutting down compute processes...')
    manager = get_manager()
    manager.shutdown_all()
    logger.info('Application shutdown complete')

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)
```

## Application Lifecycle

### Startup Phase

When the application starts:

1. **Database Initialization**
   ```python
   await init_db()
   ```
   - Creates database tables if they don't exist
   - Applies any pending migrations (if using auto-migrate)

2. **Logging Setup**
   ```python
   logging.basicConfig(
       level=logging.DEBUG if settings.debug else logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
   )
   ```

### Shutdown Phase

When the application shuts down:

1. **Compute Engine Cleanup**
   ```python
   manager = get_manager()
   manager.shutdown_all()
   ```
   - Sends shutdown commands to all active compute engines
   - Waits for processes to terminate
   - Forcefully kills processes that don't respond

## Middleware Configuration

### CORS Middleware

Cross-Origin Resource Sharing is configured to allow frontend access:

```python
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.cors_origins_list,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization'],
)
```

**Default Origins** (from `config.py`):
```python
cors_origins: str = (
    'http://localhost:3000,'
    'http://127.0.0.1:3000,'
    'http://0.0.0.0:3000,'
    # ... network IPs
)
```

## Router Registration

Routes are organized hierarchically:

```python
# main.py
from api import router
app.include_router(router)

# api/router.py
from fastapi import APIRouter
from api.v1 import router as v1_router

router = APIRouter(prefix='/api')
router.include_router(v1_router)

# api/v1/router.py
from fastapi import APIRouter
from modules.analysis.routes import router as analysis_router
from modules.datasource.routes import router as datasource_router
from modules.compute.routes import router as compute_router
from modules.results.routes import router as results_router
from modules.health.routes import router as health_router

router = APIRouter(prefix='/v1')
router.include_router(analysis_router, prefix='/analysis', tags=['Analysis'])
router.include_router(datasource_router, prefix='/datasource', tags=['DataSource'])
router.include_router(compute_router, prefix='/compute', tags=['Compute'])
router.include_router(results_router, prefix='/results', tags=['Results'])
router.include_router(health_router, prefix='/health', tags=['Health'])
```

**Resulting Routes**:
```
/api/v1/analysis/*
/api/v1/datasource/*
/api/v1/compute/*
/api/v1/results/*
/api/v1/health/*
```

## Root Endpoint

A simple root endpoint for basic health checking:

```python
@app.get('/')
async def root():
    return {'message': 'Welcome to Polars-FastAPI-Svelte Analysis Platform'}
```

## Server Configuration

### Development Server

```python
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        reload=True  # Hot reload for development
    )
```

**Run Command**:
```bash
uv run main.py
# or
uv run uvicorn main:app --reload --port 8000
```

### Production Server

```bash
uv run uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --no-reload
```

## Dependency Injection

FastAPI's dependency injection is used throughout:

### Database Session

```python
# core/database.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# Usage in routes
@router.get('/{id}')
async def get_item(
    id: str,
    session: AsyncSession = Depends(get_db)
):
    return await service.get_item(session, id)
```

### Process Manager

```python
# modules/compute/manager.py
def get_manager() -> ProcessManager:
    return ProcessManager()  # Returns singleton

# Usage in routes
@router.post('/execute')
async def execute(
    data: ExecuteSchema,
    session: AsyncSession = Depends(get_db),
    manager: ProcessManager = Depends(get_manager)
):
    engine = manager.get_or_create_engine(data.analysis_id)
    # ...
```

## Error Handling

### Route-Level Pattern

```python
@router.post('')
async def create_resource(
    data: CreateSchema,
    session: AsyncSession = Depends(get_db)
):
    try:
        return await service.create(session, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Failed to create resource: {str(e)}'
        )
```

### Error Mapping

| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| `ValueError` | 400 Bad Request | Validation/business logic errors |
| `HTTPException` | Various | Re-raised as-is |
| `Exception` | 500 Internal Server Error | Unexpected errors |

## Logging

### Configuration

```python
import logging

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)
```

### Usage

```python
logger.info('Starting application...')
logger.debug(f'Processing analysis {analysis_id}')
logger.error(f'Failed to execute: {error}')
```

## OpenAPI Documentation

FastAPI automatically generates OpenAPI documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Customization

```python
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description='Data analysis platform with visual pipeline builder',
    docs_url='/docs',
    redoc_url='/redoc',
    openapi_url='/openapi.json'
)
```

## Configuration Reference

See `core/config.py` for all settings:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `app_name` | str | Platform name | Application title |
| `app_version` | str | 1.0.0 | Version string |
| `debug` | bool | False | Enable debug mode |
| `cors_origins` | str | localhost:3000,... | Comma-separated origins |
| `database_url` | str | sqlite+aiosqlite:///... | Database connection |
| `upload_dir` | Path | ./data/uploads | Upload directory |
| `results_dir` | Path | ./data/results | Results directory |
| `max_upload_size` | int | 10GB | Max file upload size |
| `compute_timeout` | int | 300 | Compute timeout (seconds) |
| `job_ttl` | int | 3600 | Job TTL (seconds) |

## See Also

- [Modules](./modules/README.md) - Feature module documentation
- [Database](./database/README.md) - Database setup
- [Compute Engine](./compute-engine/README.md) - Compute documentation
