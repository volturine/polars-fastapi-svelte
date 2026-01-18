# Backend Documentation

Comprehensive documentation for the FastAPI backend of the Polars-FastAPI-Svelte Analysis Platform.

## Overview

The backend is a **FastAPI** application that provides:
- RESTful API for managing analyses and data sources
- Async database operations with SQLAlchemy
- Multiprocessing compute engine for Polars transformations
- File upload and storage management
- Result export in multiple formats

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | Latest |
| Language | Python | 3.13.* |
| Server | Uvicorn | Latest |
| ORM | SQLAlchemy | >=2.0 |
| Database | SQLite | - |
| DB Driver | aiosqlite | Latest |
| Migrations | Alembic | >=1.18 |
| Validation | Pydantic | >=2.0 |
| Data Processing | Polars | Latest |
| Package Manager | UV | Latest |

## Contents

| Document | Description |
|----------|-------------|
| [Application](./application.md) | FastAPI app setup, lifecycle, middleware |
| [Modules](./modules/README.md) | Feature module documentation |
| [Database](./database/README.md) | Database setup, models, migrations |
| [Compute Engine](./compute-engine/README.md) | Polars execution engine |

## Project Structure

```
backend/
├── main.py                    # Application entry point
├── pyproject.toml            # Dependencies and configuration
├── uv.lock                   # Lock file for reproducibility
│
├── core/                     # Core application components
│   ├── config.py            # Pydantic settings
│   └── database.py          # SQLAlchemy setup
│
├── api/                      # API routing
│   ├── router.py            # /api prefix router
│   └── v1/
│       └── router.py        # Version 1 routes
│
├── modules/                  # Feature modules
│   ├── analysis/            # Analysis CRUD
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routes.py
│   │   └── service.py
│   ├── datasource/          # Data source management
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routes.py
│   │   └── service.py
│   ├── compute/             # Computation engine
│   │   ├── engine.py
│   │   ├── manager.py
│   │   ├── step_converter.py
│   │   ├── schemas.py
│   │   ├── routes.py
│   │   └── service.py
│   ├── results/             # Result handling
│   │   ├── schemas.py
│   │   ├── routes.py
│   │   └── service.py
│   └── health/              # Health checks
│       ├── routes.py
│       └── service.py
│
├── database/                 # Database files
│   ├── alembic.ini          # Alembic configuration
│   ├── alembic/             # Migration versions
│   └── app.db               # SQLite database
│
├── data/                     # Runtime data
│   ├── uploads/             # Uploaded files
│   └── results/             # Computed results
│
└── tests/                    # Test suite
    ├── conftest.py          # Fixtures
    └── test_*.py            # Test files
```

## Quick Start

```bash
# Navigate to backend
cd backend

# Install dependencies
uv sync

# Run migrations
./migrate.sh upgrade

# Start development server
uv run uvicorn main:app --reload --port 8000

# Access API documentation
open http://localhost:8000/docs
```

## Key Concepts

### Module Pattern

Each feature module follows a consistent structure:

```
module/
├── models.py    # SQLAlchemy ORM models
├── schemas.py   # Pydantic request/response schemas
├── routes.py    # FastAPI route handlers
└── service.py   # Business logic
```

**Flow**: Request → Routes → Service → Models/Database

### Async Throughout

All database and I/O operations use async/await:

```python
@router.get('/{id}')
async def get_item(id: str, session: AsyncSession = Depends(get_db)):
    return await service.get_item(session, id)
```

### Compute Isolation

CPU-intensive Polars operations run in separate processes:

```python
manager = ProcessManager()  # Singleton
engine = manager.get_or_create_engine(analysis_id)
engine.execute(job_id, datasource_config, steps)
```

## Configuration

Configuration is managed via Pydantic Settings in `core/config.py`:

```python
class Settings(BaseSettings):
    app_name: str = 'Polars-FastAPI-Svelte Analysis Platform'
    debug: bool = False
    database_url: str = 'sqlite+aiosqlite:///./database/app.db'
    upload_dir: Path = Path('./data/uploads')
    results_dir: Path = Path('./data/results')
    max_upload_size: int = 10 * 1024 * 1024 * 1024  # 10GB
    engine_idle_timeout: int = 300  # 5 minutes
```

Environment variables override defaults:
```bash
export DEBUG=true
export DATABASE_URL=sqlite+aiosqlite:///./database/prod.db
```

## API Versioning

APIs are versioned under `/api/v1/`:

| Endpoint | Description |
|----------|-------------|
| `/api/v1/analysis` | Analysis management |
| `/api/v1/datasource` | Data source management |
| `/api/v1/compute` | Pipeline execution |
| `/api/v1/results` | Result retrieval |
| `/api/v1/health` | Health checks |

## Development Commands

```bash
# Run development server
uv run uvicorn main:app --reload --port 8000

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=.

# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Create migration
./migrate.sh create "migration message"

# Apply migrations
./migrate.sh upgrade

# Rollback migration
./migrate.sh downgrade
```

## See Also

- [Application](./application.md) - Detailed app configuration
- [Modules](./modules/README.md) - Module documentation
- [Database](./database/README.md) - Database documentation
- [Compute Engine](./compute-engine/README.md) - Compute documentation
