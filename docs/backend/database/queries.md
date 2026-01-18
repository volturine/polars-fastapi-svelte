# Common Query Patterns

Documentation of query patterns used throughout the application with SQLAlchemy 2.0 async.

## Overview

All database operations use SQLAlchemy 2.0+ with async/await. The patterns below demonstrate common CRUD operations.

## Basic Queries

### Select Single Record

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_analysis(session: AsyncSession, analysis_id: str) -> Analysis | None:
    result = await session.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )
    return result.scalar_one_or_none()
```

### Select All Records

```python
async def list_analyses(session: AsyncSession) -> list[Analysis]:
    result = await session.execute(select(Analysis))
    return result.scalars().all()
```

### Select with Filter

```python
async def get_analyses_by_status(
    session: AsyncSession,
    status: str
) -> list[Analysis]:
    result = await session.execute(
        select(Analysis).where(Analysis.status == status)
    )
    return result.scalars().all()
```

### Select with Multiple Conditions

```python
async def find_analysis(
    session: AsyncSession,
    name: str,
    status: str
) -> Analysis | None:
    result = await session.execute(
        select(Analysis).where(
            Analysis.name == name,
            Analysis.status == status
        )
    )
    return result.scalar_one_or_none()
```

## Creating Records

### Simple Insert

```python
import uuid
from datetime import UTC, datetime

async def create_analysis(
    session: AsyncSession,
    data: AnalysisCreateSchema
) -> Analysis:
    analysis = Analysis(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        pipeline_definition={'steps': [], 'datasource_ids': []},
        status='draft',
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.add(analysis)
    await session.commit()
    await session.refresh(analysis)

    return analysis
```

### Insert with Relationship

```python
async def create_analysis_with_datasources(
    session: AsyncSession,
    data: AnalysisCreateSchema
) -> Analysis:
    analysis_id = str(uuid.uuid4())
    now = datetime.now(UTC)

    # Create main record
    analysis = Analysis(
        id=analysis_id,
        name=data.name,
        pipeline_definition={
            'steps': [step.model_dump() for step in data.pipeline_steps],
            'datasource_ids': data.datasource_ids,
        },
        status='draft',
        created_at=now,
        updated_at=now,
    )
    session.add(analysis)

    # Create junction records
    for datasource_id in data.datasource_ids:
        link = AnalysisDataSource(
            analysis_id=analysis_id,
            datasource_id=datasource_id,
        )
        session.add(link)

    await session.commit()
    await session.refresh(analysis)

    return analysis
```

## Updating Records

### Partial Update

```python
async def update_analysis(
    session: AsyncSession,
    analysis_id: str,
    data: AnalysisUpdateSchema
) -> Analysis:
    # Fetch existing record
    result = await session.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise ValueError(f'Analysis {analysis_id} not found')

    # Apply updates conditionally
    if data.name is not None:
        analysis.name = data.name

    if data.description is not None:
        analysis.description = data.description

    if data.status is not None:
        analysis.status = data.status

    analysis.updated_at = datetime.now(UTC)

    await session.commit()
    await session.refresh(analysis)

    return analysis
```

### Update JSON Field

```python
async def update_pipeline_steps(
    session: AsyncSession,
    analysis_id: str,
    steps: list[dict]
) -> Analysis:
    result = await session.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise ValueError(f'Analysis {analysis_id} not found')

    # Modify JSON field
    analysis.pipeline_definition = {
        **analysis.pipeline_definition,
        'steps': steps
    }
    analysis.updated_at = datetime.now(UTC)

    await session.commit()
    await session.refresh(analysis)

    return analysis
```

## Deleting Records

### Simple Delete

```python
async def delete_analysis(
    session: AsyncSession,
    analysis_id: str
) -> None:
    result = await session.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise ValueError(f'Analysis {analysis_id} not found')

    await session.delete(analysis)
    await session.commit()
```

### Delete with Related Records

```python
from sqlalchemy import delete

async def delete_analysis_with_links(
    session: AsyncSession,
    analysis_id: str
) -> None:
    # Verify exists
    result = await session.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise ValueError(f'Analysis {analysis_id} not found')

    # Delete junction records first
    await session.execute(
        delete(AnalysisDataSource).where(
            AnalysisDataSource.analysis_id == analysis_id
        )
    )

    # Delete main record
    await session.delete(analysis)
    await session.commit()
```

### Bulk Delete

```python
async def delete_old_analyses(
    session: AsyncSession,
    before_date: datetime
) -> int:
    result = await session.execute(
        delete(Analysis).where(
            Analysis.created_at < before_date
        )
    )
    await session.commit()
    return result.rowcount
```

## Junction Table Operations

### Check Existing Link

```python
async def is_datasource_linked(
    session: AsyncSession,
    analysis_id: str,
    datasource_id: str
) -> bool:
    result = await session.execute(
        select(AnalysisDataSource).where(
            AnalysisDataSource.analysis_id == analysis_id,
            AnalysisDataSource.datasource_id == datasource_id,
        )
    )
    return result.scalar_one_or_none() is not None
```

### Link Records

```python
async def link_datasource(
    session: AsyncSession,
    analysis_id: str,
    datasource_id: str
) -> None:
    # Verify analysis exists
    result = await session.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )
    if not result.scalar_one_or_none():
        raise ValueError(f'Analysis {analysis_id} not found')

    # Verify datasource exists
    result = await session.execute(
        select(DataSource).where(DataSource.id == datasource_id)
    )
    if not result.scalar_one_or_none():
        raise ValueError(f'DataSource {datasource_id} not found')

    # Check if already linked
    result = await session.execute(
        select(AnalysisDataSource).where(
            AnalysisDataSource.analysis_id == analysis_id,
            AnalysisDataSource.datasource_id == datasource_id,
        )
    )
    if result.scalar_one_or_none():
        return  # Already linked

    # Create link
    link = AnalysisDataSource(
        analysis_id=analysis_id,
        datasource_id=datasource_id,
    )
    session.add(link)
    await session.commit()
```

### Unlink Records

```python
async def unlink_datasource(
    session: AsyncSession,
    analysis_id: str,
    datasource_id: str
) -> None:
    await session.execute(
        delete(AnalysisDataSource).where(
            AnalysisDataSource.analysis_id == analysis_id,
            AnalysisDataSource.datasource_id == datasource_id,
        )
    )
    await session.commit()
```

## Advanced Queries

### Ordering Results

```python
from sqlalchemy import desc

async def list_recent_analyses(
    session: AsyncSession,
    limit: int = 10
) -> list[Analysis]:
    result = await session.execute(
        select(Analysis)
        .order_by(desc(Analysis.updated_at))
        .limit(limit)
    )
    return result.scalars().all()
```

### Pagination

```python
async def list_analyses_paginated(
    session: AsyncSession,
    page: int = 1,
    per_page: int = 20
) -> list[Analysis]:
    offset = (page - 1) * per_page
    result = await session.execute(
        select(Analysis)
        .order_by(Analysis.created_at)
        .offset(offset)
        .limit(per_page)
    )
    return result.scalars().all()
```

### Count Records

```python
from sqlalchemy import func

async def count_analyses_by_status(
    session: AsyncSession,
    status: str
) -> int:
    result = await session.execute(
        select(func.count(Analysis.id)).where(
            Analysis.status == status
        )
    )
    return result.scalar() or 0
```

### Exists Check

```python
from sqlalchemy import exists

async def analysis_exists(
    session: AsyncSession,
    analysis_id: str
) -> bool:
    result = await session.execute(
        select(exists().where(Analysis.id == analysis_id))
    )
    return result.scalar() or False
```

## Transaction Patterns

### Explicit Transaction

```python
async def complex_operation(session: AsyncSession) -> None:
    async with session.begin():
        # All operations in this block are in a transaction
        analysis = Analysis(...)
        session.add(analysis)

        link = AnalysisDataSource(...)
        session.add(link)

        # Commit happens automatically at end of block
```

### Nested Operations

```python
async def create_analysis_with_validation(
    session: AsyncSession,
    data: AnalysisCreateSchema
) -> Analysis:
    # Validate all datasources exist first
    for ds_id in data.datasource_ids:
        result = await session.execute(
            select(DataSource).where(DataSource.id == ds_id)
        )
        if not result.scalar_one_or_none():
            raise ValueError(f'DataSource {ds_id} not found')

    # All validations passed, create records
    analysis = Analysis(...)
    session.add(analysis)

    for ds_id in data.datasource_ids:
        link = AnalysisDataSource(
            analysis_id=analysis.id,
            datasource_id=ds_id
        )
        session.add(link)

    await session.commit()
    await session.refresh(analysis)

    return analysis
```

## Result Handling

### scalar_one_or_none()

Returns a single scalar value or None. Raises exception if multiple results.

```python
result = await session.execute(
    select(Analysis).where(Analysis.id == id)
)
analysis = result.scalar_one_or_none()  # Analysis | None
```

### scalars().all()

Returns list of scalar values (the first column of each row).

```python
result = await session.execute(select(Analysis))
analyses = result.scalars().all()  # list[Analysis]
```

### scalar()

Returns first column of first row.

```python
result = await session.execute(
    select(func.count(Analysis.id))
)
count = result.scalar()  # int
```

## Error Handling

### Pattern Used in Services

```python
async def get_analysis(
    session: AsyncSession,
    analysis_id: str
) -> AnalysisResponseSchema:
    result = await session.execute(
        select(Analysis).where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise ValueError(f'Analysis {analysis_id} not found')

    return AnalysisResponseSchema.model_validate(analysis)
```

### In Routes

```python
@router.get('/{analysis_id}')
async def get_analysis(
    analysis_id: str,
    session: AsyncSession = Depends(get_db)
):
    try:
        return await service.get_analysis(session, analysis_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## See Also

- [Setup](./setup.md) - Database configuration
- [Models](./models.md) - SQLAlchemy ORM models
- [Migrations](./migrations.md) - Alembic migration system
