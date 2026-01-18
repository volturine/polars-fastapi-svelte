# Testing Guide

Comprehensive guide to testing the backend and frontend.

## Backend Testing

### Setup

Tests use pytest with async support:

```bash
cd backend
uv sync --extra dev
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_analysis.py

# Run tests matching pattern
uv run pytest -k "test_create"

# Run with coverage
uv run pytest --cov=modules

# Run with coverage report
uv run pytest --cov=modules --cov-report=html
```

### Test Configuration

`pytest.ini` or `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

### Writing Backend Tests

#### Test File Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_analysis.py     # Analysis module tests
├── test_datasource.py   # Datasource module tests
├── test_compute.py      # Compute module tests
└── test_integration.py  # Integration tests
```

#### Fixtures

Located in `tests/conftest.py`:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base

@pytest.fixture
async def engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def session(engine):
    """Create test database session."""
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()
```

#### Example Test - Service Layer

```python
import pytest
import uuid
from datetime import UTC, datetime

from modules.analysis.models import Analysis
from modules.analysis.service import get_analysis, create_analysis

@pytest.fixture
async def sample_analysis(session):
    """Create a sample analysis for testing."""
    analysis = Analysis(
        id=str(uuid.uuid4()),
        name="Test Analysis",
        pipeline_definition={},
        status="draft",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(analysis)
    await session.commit()
    return analysis

async def test_get_analysis(session, sample_analysis):
    """Test retrieving an analysis by ID."""
    result = await get_analysis(session, sample_analysis.id)
    assert result.name == "Test Analysis"
    assert result.status == "draft"

async def test_get_analysis_not_found(session):
    """Test error when analysis doesn't exist."""
    with pytest.raises(ValueError, match="not found"):
        await get_analysis(session, "nonexistent-id")

async def test_create_analysis(session):
    """Test creating a new analysis."""
    result = await create_analysis(
        session,
        name="New Analysis",
        description="Test description",
        datasource_ids=[],
        pipeline_steps=[],
        tabs=[]
    )
    assert result.name == "New Analysis"
    assert result.id is not None
```

#### Example Test - API Routes

```python
import pytest
from httpx import AsyncClient
from fastapi import FastAPI

from main import app

@pytest.fixture
async def client():
    """Create test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

async def test_health_endpoint(client):
    """Test health check endpoint."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

async def test_create_analysis_endpoint(client):
    """Test analysis creation via API."""
    response = await client.post(
        "/api/v1/analyses",
        json={
            "name": "Test Analysis",
            "datasource_ids": [],
            "pipeline_steps": [],
            "tabs": []
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Analysis"
```

#### Testing Compute Engine

```python
import pytest
import polars as pl
import tempfile
from pathlib import Path

from modules.compute.engine import PolarsComputeEngine

@pytest.fixture
def sample_csv():
    """Create sample CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("name,age,city\n")
        f.write("Alice,25,NYC\n")
        f.write("Bob,30,LA\n")
        f.write("Charlie,35,Chicago\n")
        yield f.name
    Path(f.name).unlink()

def test_filter_operation(sample_csv):
    """Test filter operation in compute engine."""
    engine = PolarsComputeEngine("test-analysis")

    datasource_config = {
        "source_type": "file",
        "file_path": sample_csv,
        "file_type": "csv"
    }

    pipeline_steps = [{
        "id": "step-1",
        "type": "filter",
        "config": {
            "conditions": [{"column": "age", "operator": ">", "value": 25}],
            "logic": "AND"
        },
        "depends_on": []
    }]

    engine.start()
    job_id = engine.execute(datasource_config, pipeline_steps)

    # Wait for result
    result = None
    for _ in range(10):
        result = engine.get_result(timeout=1.0)
        if result and result.get("status") == "completed":
            break

    engine.shutdown()

    assert result is not None
    assert result["status"] == "completed"
    assert result["data"]["row_count"] == 2  # Bob and Charlie
```

### Testing Best Practices

1. **Isolate tests**: Each test should be independent
2. **Use fixtures**: Share setup code via fixtures
3. **Test edge cases**: Empty data, null values, errors
4. **Mock external services**: Don't hit real APIs/databases
5. **Clean up**: Remove temp files, close connections

## Frontend Testing

### Setup

Tests use Vitest with Testing Library:

```bash
cd frontend
npm install
```

### Running Tests

```bash
# Run all tests
npm run test

# Run in watch mode
npm run test:watch

# Run specific directory
npm run test -- src/lib/components

# Run with UI
npm run test -- --ui

# Run with coverage
npm run test -- --coverage
```

### Test Configuration

`vite.config.ts`:

```typescript
import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
    plugins: [svelte({ hot: !process.env.VITEST })],
    test: {
        include: ['src/**/*.{test,spec}.{js,ts}'],
        environment: 'jsdom',
        globals: true,
        setupFiles: ['src/setupTests.ts']
    }
});
```

### Writing Frontend Tests

#### Test File Structure

```
src/lib/
├── components/
│   ├── common/
│   │   ├── ConfirmDialog.svelte
│   │   └── ConfirmDialog.test.ts
│   ├── operations/
│   │   ├── FilterConfig.svelte
│   │   └── FilterConfig.test.ts
│   └── gallery/
│       ├── AnalysisCard.svelte
│       └── AnalysisCard.test.ts
└── stores/
    ├── analysis.svelte.ts
    └── analysis.svelte.test.ts
```

#### Example Test - Component

```typescript
import { render, fireEvent, screen } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import ConfirmDialog from './ConfirmDialog.svelte';

describe('ConfirmDialog', () => {
    it('renders with title and message', () => {
        render(ConfirmDialog, {
            props: {
                open: true,
                title: 'Confirm Action',
                message: 'Are you sure?',
                onConfirm: vi.fn(),
                onCancel: vi.fn()
            }
        });

        expect(screen.getByText('Confirm Action')).toBeInTheDocument();
        expect(screen.getByText('Are you sure?')).toBeInTheDocument();
    });

    it('calls onConfirm when confirm button clicked', async () => {
        const onConfirm = vi.fn();
        render(ConfirmDialog, {
            props: {
                open: true,
                title: 'Confirm',
                message: 'Proceed?',
                onConfirm,
                onCancel: vi.fn()
            }
        });

        await fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
        expect(onConfirm).toHaveBeenCalled();
    });

    it('calls onCancel when cancel button clicked', async () => {
        const onCancel = vi.fn();
        render(ConfirmDialog, {
            props: {
                open: true,
                title: 'Confirm',
                message: 'Proceed?',
                onConfirm: vi.fn(),
                onCancel
            }
        });

        await fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
        expect(onCancel).toHaveBeenCalled();
    });
});
```

#### Example Test - Operation Config

```typescript
import { render, fireEvent, screen } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import FilterConfig from './FilterConfig.svelte';

describe('FilterConfig', () => {
    const defaultProps = {
        config: {
            conditions: [{ column: '', operator: '==', value: '' }],
            logic: 'AND' as const
        },
        schema: {
            columns: [
                { name: 'age', dtype: 'Int64', nullable: false },
                { name: 'name', dtype: 'String', nullable: true }
            ],
            row_count: 100
        },
        onConfigChange: vi.fn()
    };

    it('renders column selector', () => {
        render(FilterConfig, { props: defaultProps });
        expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('calls onConfigChange when condition added', async () => {
        const onConfigChange = vi.fn();
        render(FilterConfig, {
            props: { ...defaultProps, onConfigChange }
        });

        await fireEvent.click(screen.getByText('Add Condition'));
        expect(onConfigChange).toHaveBeenCalled();
    });
});
```

#### Example Test - Store

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { AnalysisStore } from './analysis.svelte';

describe('AnalysisStore', () => {
    let store: AnalysisStore;

    beforeEach(() => {
        store = new AnalysisStore();
    });

    it('initializes with null current analysis', () => {
        expect(store.current).toBeNull();
    });

    it('sets current analysis', () => {
        const analysis = {
            id: 'test-id',
            name: 'Test Analysis',
            description: null,
            pipeline_definition: {},
            status: 'draft',
            created_at: '2024-01-01',
            updated_at: '2024-01-01',
            result_path: null,
            thumbnail: null,
            tabs: []
        };

        store.setCurrent(analysis);
        expect(store.current).toEqual(analysis);
    });

    it('adds new tab', () => {
        store.addTab({
            id: 'tab-1',
            name: 'Tab 1',
            type: 'datasource',
            parent_id: null,
            datasource_id: 'ds-1',
            steps: []
        });

        expect(store.tabs).toHaveLength(1);
        expect(store.tabs[0].name).toBe('Tab 1');
    });

    it('computes active tab correctly', () => {
        store.addTab({
            id: 'tab-1',
            name: 'Tab 1',
            type: 'datasource',
            parent_id: null,
            datasource_id: 'ds-1',
            steps: []
        });

        store.setActiveTab('tab-1');
        expect(store.activeTab?.id).toBe('tab-1');
    });
});
```

#### Mocking API Calls

```typescript
import { vi } from 'vitest';
import * as client from '$lib/api/client';

// Mock the entire module
vi.mock('$lib/api/client', () => ({
    apiRequestSafe: vi.fn()
}));

describe('Component with API', () => {
    it('fetches data on mount', async () => {
        const mockData = { id: '1', name: 'Test' };
        vi.mocked(client.apiRequestSafe).mockResolvedValue({
            isOk: () => true,
            value: mockData
        });

        // Render component and test...
    });
});
```

### Testing Best Practices

1. **Test behavior, not implementation**: Focus on what users see
2. **Use accessible queries**: `getByRole`, `getByLabelText`
3. **Avoid testing library internals**: Don't test Svelte's reactivity
4. **Keep tests fast**: Mock slow operations
5. **Test error states**: Network errors, validation failures

## Integration Testing

### End-to-End Flow

```python
async def test_full_analysis_flow(client, sample_csv):
    """Test complete analysis workflow."""
    # 1. Upload datasource
    with open(sample_csv, 'rb') as f:
        response = await client.post(
            "/api/v1/datasources/upload",
            files={"file": f},
            data={"name": "Test Data"}
        )
    datasource_id = response.json()["id"]

    # 2. Create analysis
    response = await client.post(
        "/api/v1/analyses",
        json={
            "name": "Test Analysis",
            "datasource_ids": [datasource_id],
            "pipeline_steps": [{
                "id": "step-1",
                "type": "filter",
                "config": {"conditions": [...]},
                "depends_on": []
            }],
            "tabs": [...]
        }
    )
    analysis_id = response.json()["id"]

    # 3. Execute pipeline
    response = await client.post(
        f"/api/v1/compute/execute/{analysis_id}"
    )
    job_id = response.json()["job_id"]

    # 4. Poll for results
    for _ in range(30):
        response = await client.get(
            f"/api/v1/compute/status/{analysis_id}/{job_id}"
        )
        if response.json()["status"] == "completed":
            break
        await asyncio.sleep(0.5)

    # 5. Verify results
    assert response.json()["status"] == "completed"
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: |
          cd backend
          uv sync --extra dev
          uv run pytest --cov=modules

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: |
          cd frontend
          npm ci
          npm run test -- --coverage
```

## See Also

- [Development Workflow](./development-workflow.md) - Development setup
- [Contributing](../contributing/README.md) - Contribution guidelines
- [Backend Documentation](../backend/README.md) - Backend architecture
