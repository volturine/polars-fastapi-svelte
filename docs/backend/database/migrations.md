# Database Migrations

Complete guide to managing database schema changes with Alembic.

## Overview

Alembic handles database migrations with async support. It tracks schema versions and applies changes incrementally.

## File Structure

```
backend/database/
├── alembic.ini              # Main Alembic configuration
└── alembic/
    ├── env.py               # Migration environment (async)
    ├── script.py.mako       # Migration template
    └── versions/            # Migration files
        └── a7fc1ff5a710_initial_migration.py
```

## Configuration

### alembic.ini

```ini
[alembic]
script_location = alembic
prepend_sys_path = ..
version_path_separator = os

[logging]
level = WARN
handlers = console
```

### env.py (Async Setup)

```python
import asyncio
from sqlalchemy.ext.asyncio import async_engine_from_config

from core.config import settings
from core.database import Base

# Import all models for autogenerate
from modules.analysis.models import Analysis, AnalysisDataSource
from modules.datasource.models import DataSource

target_metadata = Base.metadata

async def run_async_migrations():
    """Run migrations in async mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())
```

### SQLite Batch Mode

SQLite requires batch mode for ALTER operations:

```python
def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,  # Required for SQLite
    )
```

## Common Commands

### Run from backend directory

```bash
cd backend
```

### Check Current Version

```bash
alembic current
```

### View Migration History

```bash
alembic history --verbose
```

### Upgrade to Latest

```bash
alembic upgrade head
```

### Upgrade by Steps

```bash
# Upgrade one version
alembic upgrade +1

# Upgrade to specific version
alembic upgrade a7fc1ff5a710
```

### Downgrade

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade a7fc1ff5a710

# Downgrade to base (empty database)
alembic downgrade base
```

### Generate Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Add user table"

# Create empty migration
alembic revision -m "Custom migration"
```

## Creating Migrations

### Step 1: Modify Models

```python
# modules/user/models.py
class User(Base):
    __tablename__ = 'users'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
```

### Step 2: Import in env.py

```python
# database/alembic/env.py
from modules.user.models import User  # Add this import
```

### Step 3: Generate Migration

```bash
alembic revision --autogenerate -m "Add user table"
```

### Step 4: Review Generated File

```python
# versions/xxxx_add_user_table.py
def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

def downgrade():
    op.drop_table('users')
```

### Step 5: Apply Migration

```bash
alembic upgrade head
```

## Migration Operations

### Create Table

```python
def upgrade():
    op.create_table(
        'items',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
    )
```

### Add Column

```python
def upgrade():
    op.add_column('items', sa.Column('status', sa.String(), default='active'))
```

### Add Index

```python
def upgrade():
    op.create_index('ix_items_name', 'items', ['name'])
```

### Add Foreign Key

```python
def upgrade():
    op.add_column('items', sa.Column('user_id', sa.String()))
    op.create_foreign_key(
        'fk_items_user',
        'items', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
```

### Rename Column

```python
def upgrade():
    # SQLite requires batch mode
    with op.batch_alter_table('items') as batch_op:
        batch_op.alter_column('old_name', new_column_name='new_name')
```

### Data Migration

```python
def upgrade():
    # Create table first
    op.create_table('new_items', ...)

    # Migrate data
    connection = op.get_bind()
    connection.execute(
        text("INSERT INTO new_items SELECT * FROM old_items")
    )

    # Drop old table
    op.drop_table('old_items')
```

## SQLite-Specific Considerations

SQLite has limited ALTER TABLE support. Alembic's batch mode handles this:

```python
# This works with batch mode
def upgrade():
    with op.batch_alter_table('items') as batch_op:
        batch_op.add_column(sa.Column('new_col', sa.String()))
        batch_op.drop_column('old_col')
        batch_op.alter_column('name', nullable=False)
```

**What batch mode does**:
1. Creates a temporary table with new schema
2. Copies data from old table
3. Drops old table
4. Renames temporary table

## Migration Script

The project includes a helper script:

```bash
# backend/migrate.sh
#!/bin/bash

# Run migrations
cd "$(dirname "$0")"

# Check if alembic is available
if ! command -v alembic &> /dev/null; then
    echo "Alembic not found, using uv run..."
    uv run alembic upgrade head
else
    alembic upgrade head
fi
```

Usage:
```bash
./migrate.sh
```

## Troubleshooting

### "Target database is not up to date"

```bash
# Stamp the database with current revision
alembic stamp head
```

### "Can't locate revision"

```bash
# Check migration history
alembic history

# If corrupted, stamp to known good state
alembic stamp <revision_id>
```

### "No changes detected" (autogenerate)

Ensure models are imported in env.py:

```python
# database/alembic/env.py
from modules.analysis.models import Analysis
from modules.datasource.models import DataSource
# Add any new models here
```

### Reset Database

```bash
# Remove database file
rm database/app.db

# Apply all migrations fresh
alembic upgrade head
```

## Best Practices

1. **Review auto-generated migrations** before applying
2. **Test migrations** in development before production
3. **Never edit applied migrations** - create new ones instead
4. **Include downgrade** logic for reversibility
5. **Use descriptive messages** for migration names
6. **Commit migrations** to version control

## See Also

- [Setup](./setup.md) - Database configuration
- [Models](./models.md) - SQLAlchemy ORM models
- [Queries](./queries.md) - Common query patterns
