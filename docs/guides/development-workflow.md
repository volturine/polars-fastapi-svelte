# Development Workflow

Guide to day-to-day development on the project.

## Development Setup

### Prerequisites

```bash
# Python 3.13+ with UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node.js 18+ (recommend using nvm)
nvm install 18
nvm use 18
```

### Initial Setup

```bash
# Clone and setup
git clone <repository>
cd polars-fastapi-svelte

# Backend
cd backend
uv sync --extra dev
uv run alembic upgrade head

# Frontend
cd ../frontend
npm install
```

## Running in Development

### Using Just

```bash
# Start both services
just dev

# Or individually
just backend
just frontend
```

### Manual Start

**Terminal 1**:
```bash
cd backend
uv run main.py
```

**Terminal 2**:
```bash
cd frontend
npm run dev
```

## Code Style

### Backend (Python)

```bash
# Format code
uv run ruff format .

# Lint and auto-fix
uv run ruff check --fix .

# Type check
uv run mypy .
```

### Frontend (TypeScript/Svelte)

```bash
# Format
npm run format

# Lint
npm run lint

# Type check
npm run check
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_analysis.py

# Run tests matching pattern
uv run pytest -k "test_create"

# With coverage
uv run pytest --cov=modules
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm run test

# Watch mode
npm run test:watch

# Run specific directory
npm run test -- src/lib/components

# With UI
npm run test -- --ui
```

## Database Migrations

### Creating Migrations

```bash
cd backend

# Auto-generate from model changes
uv run alembic revision --autogenerate -m "Add user table"

# Create empty migration
uv run alembic revision -m "Custom migration"
```

### Running Migrations

```bash
# Apply all migrations
uv run alembic upgrade head

# Rollback one version
uv run alembic downgrade -1

# View current version
uv run alembic current
```

## Adding Features

### Backend Feature

1. **Create module** in `backend/modules/`
   ```
   modules/newfeature/
   ├── __init__.py
   ├── models.py      # SQLAlchemy models
   ├── schemas.py     # Pydantic schemas
   ├── routes.py      # FastAPI routes
   └── service.py     # Business logic
   ```

2. **Register routes** in `api/v1/router.py`
   ```python
   from modules.newfeature.routes import router as newfeature_router
   router.include_router(newfeature_router)
   ```

3. **Add tests** in `tests/test_newfeature.py`

### Frontend Feature

1. **Create component** in `lib/components/`
   ```
   components/newfeature/
   ├── NewComponent.svelte
   ├── NewComponent.test.ts
   └── index.ts
   ```

2. **Add route** (if page) in `routes/`

3. **Add API client** in `lib/api/`

4. **Add store** (if needed) in `lib/stores/`

## Git Workflow

### Branch Naming

```
feature/add-user-auth
fix/filter-validation
refactor/compute-engine
docs/api-reference
```

### Commit Messages

```
feat: Add user authentication
fix: Resolve filter validation error
refactor: Simplify compute engine
docs: Update API reference
test: Add filter component tests
```

### Pull Request Process

1. Create feature branch
2. Make changes
3. Run tests and linting
4. Create PR with description
5. Address review feedback
6. Squash and merge

## Debugging

### Backend

```python
# Add logging
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Processing: {data}")

# Enable debug mode
# In .env or environment:
DEBUG=true
```

### Frontend

```svelte
<script lang="ts">
    // Use $inspect for reactive debugging
    $inspect(analysisStore.pipeline);

    // Or traditional console
    $effect(() => {
        console.log('State changed:', someState);
    });
</script>
```

### API Debugging

- Swagger UI: http://localhost:8000/docs
- Check Network tab in browser DevTools
- Use `curl` or Postman for API testing

## Common Tasks

### Reset Database

```bash
cd backend
rm database/app.db
uv run alembic upgrade head
```

### Clear Frontend Cache

```bash
cd frontend
rm -rf .svelte-kit
rm -rf node_modules/.vite
npm run dev
```

### Update Dependencies

```bash
# Backend
cd backend
uv lock --upgrade
uv sync

# Frontend
cd frontend
npm update
```

## Environment Variables

### Backend (.env)

```bash
DATABASE_URL=sqlite+aiosqlite:///./database/app.db
DEBUG=false
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env)

```bash
VITE_API_URL=  # Empty for dev proxy
```

## Troubleshooting

### Port already in use

```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

### Module not found (Python)

```bash
# Ensure in backend directory
cd backend
uv sync --extra dev
```

### Type errors (Svelte)

```bash
# Regenerate types
npm run check
```

## See Also

- [Testing](./testing.md) - Detailed testing guide
- [Adding Operations](./adding-operations.md) - Extending the engine
- [Contributing](../contributing/README.md) - Contribution guidelines
