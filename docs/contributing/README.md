# Contributing

Guidelines for contributing to the Polars-FastAPI-Svelte Analysis Platform.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Set up development environment (see [Getting Started](../guides/getting-started.md))
4. Create a feature branch

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## Development Guidelines

### Code Style

#### Backend (Python)

- Use type hints everywhere
- Follow async/await patterns
- Use Pydantic for validation
- Keep routes thin, logic in services

```python
# Good
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

#### Frontend (TypeScript/Svelte)

- Use Svelte 5 runes (never legacy syntax)
- Use TypeScript strictly
- Keep components focused
- Use stores for shared state

```svelte
<!-- Good -->
<script lang="ts">
    interface Props {
        name: string;
        onSelect: (id: string) => void;
    }
    let { name, onSelect }: Props = $props();
    let selected = $state(false);
</script>
```

### Commit Messages

Use conventional commits:

```
feat: Add user authentication
fix: Resolve filter validation error
refactor: Simplify compute engine
docs: Update API documentation
test: Add filter component tests
chore: Update dependencies
```

### Pull Requests

1. **Title**: Clear, concise description
2. **Description**: What and why (not how)
3. **Tests**: Include tests for new features
4. **Docs**: Update docs if needed

#### PR Template

```markdown
## Summary
Brief description of changes

## Changes
- Added X
- Fixed Y
- Updated Z

## Testing
How to test these changes

## Checklist
- [ ] Tests pass
- [ ] Linting passes
- [ ] Documentation updated
```

## Testing Requirements

### Backend

- All new features must have tests
- Aim for >80% coverage on new code
- Use pytest fixtures

```python
@pytest.fixture
async def sample_analysis(session: AsyncSession) -> Analysis:
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

async def test_get_analysis(session: AsyncSession, sample_analysis: Analysis):
    result = await get_analysis(session, sample_analysis.id)
    assert result.name == "Test Analysis"
```

### Frontend

- Test component behavior, not implementation
- Use Testing Library
- Mock API calls

```typescript
import { render, fireEvent } from '@testing-library/svelte';
import { vi } from 'vitest';
import Component from './Component.svelte';

describe('Component', () => {
    it('calls onSelect when clicked', async () => {
        const onSelect = vi.fn();
        const { getByRole } = render(Component, {
            props: { onSelect }
        });

        await fireEvent.click(getByRole('button'));
        expect(onSelect).toHaveBeenCalled();
    });
});
```

## Adding New Features

### Adding a New Operation

1. **Backend**: Add to `engine.py`
   ```python
   elif operation == 'new_op':
       param = params.get('param')
       return lf.new_method(param)
   ```

2. **Frontend Config**: Create `NewOpConfig.svelte`

3. **Frontend Types**: Add to `operation-config.ts`

4. **Step Converter**: Add conversion in `step_converter.py`

5. **Tests**: Add backend and frontend tests

6. **Docs**: Update operations reference

### Adding a New Module

1. Create module structure:
   ```
   modules/newmodule/
   ├── __init__.py
   ├── models.py
   ├── schemas.py
   ├── routes.py
   └── service.py
   ```

2. Register in `api/v1/router.py`

3. Add tests in `tests/test_newmodule.py`

4. Document in `docs/backend/modules/`

## Documentation

### When to Document

- New features
- API changes
- Configuration changes
- Breaking changes

### Documentation Style

- Use clear, concise language
- Include code examples
- Keep formatting consistent
- Use tables for reference data

## Review Process

### For Contributors

1. Ensure CI passes
2. Respond to review comments
3. Keep PR focused (one feature per PR)

### For Reviewers

1. Be constructive
2. Suggest improvements, don't demand
3. Approve when satisfied
4. Use "Request changes" sparingly

## Release Process

1. Update version in `pyproject.toml` and `package.json`
2. Update CHANGELOG
3. Create release branch
4. Merge to main
5. Tag release

## Getting Help

- Open an issue for bugs
- Discussions for questions
- PRs for contributions

## See Also

- [Development Workflow](../guides/development-workflow.md)
- [Testing Guide](../guides/testing.md)
- [Architecture](../architecture/README.md)
