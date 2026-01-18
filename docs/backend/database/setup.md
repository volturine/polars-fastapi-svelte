# Database Setup

Complete guide to database configuration and initialization.

## Overview

The application uses SQLite with async support via aiosqlite and SQLAlchemy 2.0+. The database configuration is managed through environment variables and the `Settings` class.

## Configuration

### Settings Class

```python
# core/config.py
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    database_url: str = 'sqlite+aiosqlite:///./database/app.db'
    debug: bool = False  # Enables SQL logging
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./database/app.db` | Database connection string |
| `DEBUG` | `false` | Enable SQL query logging |

### Example `.env`

```bash
# Use default SQLite (recommended for local development)
DATABASE_URL=sqlite+aiosqlite:///./database/app.db

# Or PostgreSQL for production
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname

# Enable SQL logging for debugging
DEBUG=true
```

## Database Engine

### Engine Configuration

```python
# core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    connect_args={'check_same_thread': False}  # SQLite-specific
    if 'sqlite' in settings.database_url else {},
)
```

**Key Settings**:
- `echo`: Logs all SQL statements when `DEBUG=true`
- `check_same_thread`: Required for SQLite to work across threads

### Session Factory

```python
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects accessible after commit
)
```

**Why `expire_on_commit=False`**:
- Allows accessing object attributes after `session.commit()`
- Prevents "DetachedInstanceError" in async contexts
- Standard practice for async SQLAlchemy

## Dependency Injection

### Database Session Dependency

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

### Usage in Routes

```python
from fastapi import Depends
from core.database import get_db

@router.get('/items')
async def list_items(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Item))
    return result.scalars().all()
```

## Base Model

### Type Annotation Mapping

```python
class Base(DeclarativeBase):
    type_annotation_map = {
        dict: JSON,           # Python dict → JSON column
        datetime: DateTime(timezone=True),  # Timezone-aware datetime
    }
```

This allows using Python type hints directly:

```python
class Analysis(Base):
    # Automatically maps to JSON column
    pipeline_definition: Mapped[dict] = mapped_column(nullable=False)

    # Automatically maps to timezone-aware DateTime
    created_at: Mapped[datetime] = mapped_column(nullable=False)
```

## Initialization

### Development Initialization

```python
async def init_db():
    """Create all tables from models (development only)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### Application Startup

```python
# main.py
from core.database import init_db

@app.on_event('startup')
async def startup():
    await init_db()  # Creates tables if they don't exist
```

### Production Initialization

For production, use Alembic migrations instead:

```bash
# Run migrations
cd backend
alembic upgrade head
```

## File Structure

```
backend/
├── core/
│   ├── config.py      # Settings with DATABASE_URL
│   └── database.py    # Engine, session factory, Base
├── database/
│   ├── app.db         # SQLite database file
│   ├── alembic.ini    # Alembic configuration
│   └── alembic/       # Migration scripts
│       ├── env.py
│       └── versions/
└── modules/
    └── */models.py    # SQLAlchemy models
```

## Connection Pooling

### SQLite (Development)

SQLite uses a single file, so pooling is minimal:

```python
# Automatic with SQLite - no additional config needed
engine = create_async_engine(
    'sqlite+aiosqlite:///./database/app.db',
    connect_args={'check_same_thread': False}
)
```

### PostgreSQL (Production)

For PostgreSQL, configure pooling:

```python
engine = create_async_engine(
    'postgresql+asyncpg://user:pass@localhost/db',
    pool_size=5,        # Connections in pool
    max_overflow=10,    # Additional connections when busy
    pool_timeout=30,    # Wait time for connection
    pool_recycle=1800,  # Recycle connections after 30 min
)
```

## Troubleshooting

### Common Issues

**"Database is locked"** (SQLite):
```python
# Solution: Ensure check_same_thread=False
connect_args={'check_same_thread': False}
```

**"DetachedInstanceError"**:
```python
# Solution: Use expire_on_commit=False
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False
)
```

**"No module named 'aiosqlite'"**:
```bash
# Solution: Install the async driver
uv add aiosqlite
```

### Verifying Setup

```python
# Test connection
async def test_connection():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        print("Database connection successful!")
```

## See Also

- [Models](./models.md) - SQLAlchemy ORM models
- [Migrations](./migrations.md) - Alembic migration system
- [Queries](./queries.md) - Common query patterns
