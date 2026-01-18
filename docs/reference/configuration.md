# Configuration Reference

Complete reference for environment variables and application settings.

## Backend Configuration

The backend uses Pydantic Settings for type-safe configuration management.

### Settings Class

Located in `backend/core/config.py`:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    app_name: str = 'Polars-FastAPI-Svelte Analysis Platform'
    app_version: str = '1.0.0'
    debug: bool = False
    cors_origins: str = 'http://localhost:3000,...'
    database_url: str = 'sqlite+aiosqlite:///./database/app.db'
    upload_dir: Path = Path('./data/uploads')
    results_dir: Path = Path('./data/results')
    exports_dir: Path = Path('./data/exports')
    max_upload_size: int = 10 * 1024 * 1024 * 1024  # 10GB
    compute_timeout: int = 300  # 5 minutes
    job_ttl: int = 3600  # 1 hour
```

## Environment Variables

### Application Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APP_NAME` | string | `Polars-FastAPI-Svelte Analysis Platform` | Application display name |
| `APP_VERSION` | string | `1.0.0` | Application version |
| `DEBUG` | bool | `false` | Enable debug mode (SQL echo, verbose logging) |

### Database

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | string | `sqlite+aiosqlite:///./database/app.db` | SQLAlchemy async connection string |

#### Supported Database URLs

```bash
# SQLite (default)
DATABASE_URL=sqlite+aiosqlite:///./database/app.db

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname

# MySQL
DATABASE_URL=mysql+aiomysql://user:pass@localhost:3306/dbname
```

### CORS Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CORS_ORIGINS` | string | `http://localhost:3000,...` | Comma-separated allowed origins |

Default origins include:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://0.0.0.0:3000`

#### Example

```bash
# Single origin
CORS_ORIGINS=http://localhost:3000

# Multiple origins
CORS_ORIGINS=http://localhost:3000,https://app.example.com

# Access via property
settings.cors_origins_list  # Returns ['http://localhost:3000', ...]
```

### File Storage

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `UPLOAD_DIR` | Path | `./data/uploads` | Directory for uploaded files |
| `RESULTS_DIR` | Path | `./data/results` | Directory for computation results |
| `EXPORTS_DIR` | Path | `./data/exports` | Directory for exported files |
| `MAX_UPLOAD_SIZE` | int | `10737418240` (10GB) | Maximum file upload size in bytes |

Directories are created automatically on startup if they don't exist.

### Compute Engine

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `COMPUTE_TIMEOUT` | int | `300` | Pipeline execution timeout (seconds) |
| `JOB_TTL` | int | `3600` | Job result retention time (seconds) |

## Frontend Configuration

### Vite Environment Variables

Located in `frontend/.env`:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_API_URL` | string | (empty) | API base URL (empty = use dev proxy) |

#### Development vs Production

```bash
# Development (uses Vite proxy)
VITE_API_URL=

# Production (direct API URL)
VITE_API_URL=https://api.example.com
```

### Vite Proxy Configuration

In `frontend/vite.config.ts`:

```typescript
export default defineConfig({
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true
            }
        }
    }
});
```

## Docker Configuration

### Environment File (.env.docker)

```bash
# Backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app
CORS_ORIGINS=http://localhost:3000
DEBUG=false
UPLOAD_DIR=/app/data/uploads
RESULTS_DIR=/app/data/results
COMPUTE_TIMEOUT=600
JOB_TTL=7200

# Frontend
VITE_API_URL=http://api:8000
```

### Docker Compose

```yaml
services:
  api:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - DEBUG=${DEBUG}
    volumes:
      - uploads:/app/data/uploads
      - results:/app/data/results

  frontend:
    environment:
      - VITE_API_URL=${VITE_API_URL}
```

## Configuration Precedence

Settings are loaded in this order (later overrides earlier):

1. Default values in `Settings` class
2. `.env` file in backend directory
3. Environment variables
4. Explicit constructor arguments

## Computed Properties

### `cors_origins_list`

Parses the comma-separated `CORS_ORIGINS` string into a list:

```python
settings = Settings()
origins = settings.cors_origins_list
# ['http://localhost:3000', 'http://127.0.0.1:3000', ...]
```

## Debug Mode

When `DEBUG=true`:

- SQL queries are echoed to console
- Verbose logging is enabled
- Stack traces shown in API responses
- Hot reload enabled

```bash
# Enable debug mode
DEBUG=true

# In Python
if settings.debug:
    logger.setLevel(logging.DEBUG)
```

## Example .env Files

### Backend Development (.env)

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./database/app.db

# Debug
DEBUG=true

# CORS (frontend dev server)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Compute
COMPUTE_TIMEOUT=300
JOB_TTL=3600

# Storage
UPLOAD_DIR=./data/uploads
RESULTS_DIR=./data/results
MAX_UPLOAD_SIZE=10737418240
```

### Frontend Development (.env)

```bash
# Empty for dev proxy, or set explicit URL
VITE_API_URL=
```

### Production (.env.production)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:secure_password@db.example.com:5432/production

# Security
DEBUG=false
CORS_ORIGINS=https://app.example.com

# Extended timeouts for production workloads
COMPUTE_TIMEOUT=600
JOB_TTL=86400

# Persistent storage
UPLOAD_DIR=/var/app/uploads
RESULTS_DIR=/var/app/results
```

## See Also

- [Getting Started](../guides/getting-started.md) - Initial setup
- [Development Workflow](../guides/development-workflow.md) - Development configuration
- [Backend Documentation](../backend/README.md) - Backend architecture
