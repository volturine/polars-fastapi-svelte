# Adding Operations

Guide to extending the compute engine with new Polars operations.

## Overview

Adding a new operation involves changes to both backend and frontend:

1. **Backend**: Add operation logic to `engine.py`
2. **Backend**: Add config converter to `step_converter.py`
3. **Frontend**: Create configuration component
4. **Frontend**: Add TypeScript types
5. **Tests**: Add backend and frontend tests
6. **Docs**: Update operations reference

## Step 1: Backend - Engine Implementation

### Location

`backend/modules/compute/engine.py` - `_apply_step()` method

### Add Operation Handler

```python
@staticmethod
def _apply_step(lf: pl.LazyFrame, step: dict) -> pl.LazyFrame:
    """Apply a single transformation step to the LazyFrame."""
    operation = step.get('operation')
    params = step.get('params', {})

    # ... existing operations ...

    elif operation == 'new_operation':
        # Extract parameters
        column = params.get('column')
        option = params.get('option', 'default')

        # Validate required parameters
        if not column:
            raise ValueError('new_operation requires a column parameter')

        # Apply Polars transformation
        return lf.with_columns(
            pl.col(column).some_method(option).alias(f'{column}_transformed')
        )

    else:
        raise ValueError(f'Unsupported operation: {operation}')
```

### Parameter Guidelines

- Use `params.get('key', default)` for optional parameters
- Raise `ValueError` for missing required parameters
- Use descriptive error messages
- Return a `LazyFrame` (maintain lazy evaluation)

### Example: Adding `rolling` Operation

```python
elif operation == 'rolling':
    column = params.get('column')
    window_size = params.get('window_size', 3)
    function = params.get('function', 'mean')
    new_column = params.get('new_column')

    if not column:
        raise ValueError('Rolling requires a column parameter')

    col_expr = pl.col(column)

    if function == 'mean':
        rolling_expr = col_expr.rolling_mean(window_size)
    elif function == 'sum':
        rolling_expr = col_expr.rolling_sum(window_size)
    elif function == 'std':
        rolling_expr = col_expr.rolling_std(window_size)
    elif function == 'min':
        rolling_expr = col_expr.rolling_min(window_size)
    elif function == 'max':
        rolling_expr = col_expr.rolling_max(window_size)
    else:
        raise ValueError(f'Unsupported rolling function: {function}')

    output_name = new_column or f'{column}_rolling_{function}'
    return lf.with_columns(rolling_expr.alias(output_name))
```

## Step 2: Backend - Step Converter

### Location

`backend/modules/compute/step_converter.py`

### Add Converter Function

```python
def convert_rolling_config(config: dict) -> dict:
    """Convert rolling config from frontend to backend format.

    Frontend: {column, windowSize, function, newColumn}
    Backend: {column, window_size, function, new_column}
    """
    return {
        'column': config.get('column'),
        # Support both camelCase and snake_case
        'window_size': config.get('windowSize') or config.get('window_size', 3),
        'function': config.get('function', 'mean'),
        'new_column': config.get('newColumn') or config.get('new_column'),
    }
```

### Register Converter

Add to `get_converters()`:

```python
def get_converters() -> dict:
    """Return all converters dictionary."""
    return {
        # ... existing converters ...
        'rolling': convert_rolling_config,
    }
```

### Converter Guidelines

- Support both camelCase (frontend) and snake_case (backend)
- Provide sensible defaults
- Handle missing fields gracefully
- Document format conversion in docstring

## Step 3: Frontend - TypeScript Types

### Location

`frontend/src/lib/types/operation-config.ts`

### Add Config Interface

```typescript
export interface RollingConfigData {
    column: string;
    windowSize: number;
    function: 'mean' | 'sum' | 'std' | 'min' | 'max';
    newColumn?: string;
}
```

### Update Union Type

```typescript
export type OperationConfig =
    | FilterConfigData
    | SelectConfigData
    // ... existing types ...
    | RollingConfigData;
```

## Step 4: Frontend - Configuration Component

### Location

`frontend/src/lib/components/operations/RollingConfig.svelte`

### Component Template

```svelte
<script lang="ts">
    import type { RollingConfigData } from '$lib/types/operation-config';
    import type { SchemaInfo } from '$lib/types/datasource';

    interface Props {
        config: RollingConfigData;
        schema: SchemaInfo | null;
        onConfigChange: (config: RollingConfigData) => void;
    }

    let { config, schema, onConfigChange }: Props = $props();

    // Get numeric columns for selection
    const numericColumns = $derived(
        schema?.columns.filter(col =>
            col.dtype.includes('Int') || col.dtype.includes('Float')
        ) ?? []
    );

    // Available rolling functions
    const functions = [
        { value: 'mean', label: 'Mean' },
        { value: 'sum', label: 'Sum' },
        { value: 'std', label: 'Std Dev' },
        { value: 'min', label: 'Min' },
        { value: 'max', label: 'Max' }
    ];

    function updateConfig<K extends keyof RollingConfigData>(
        key: K,
        value: RollingConfigData[K]
    ) {
        onConfigChange({ ...config, [key]: value });
    }
</script>

<div class="config-panel">
    <div class="field">
        <label for="column">Column</label>
        <select
            id="column"
            value={config.column}
            onchange={(e) => updateConfig('column', e.currentTarget.value)}
        >
            <option value="">Select column...</option>
            {#each numericColumns as col}
                <option value={col.name}>{col.name} ({col.dtype})</option>
            {/each}
        </select>
    </div>

    <div class="field">
        <label for="windowSize">Window Size</label>
        <input
            id="windowSize"
            type="number"
            min="2"
            value={config.windowSize}
            onchange={(e) => updateConfig('windowSize', parseInt(e.currentTarget.value))}
        />
    </div>

    <div class="field">
        <label for="function">Function</label>
        <select
            id="function"
            value={config.function}
            onchange={(e) => updateConfig('function', e.currentTarget.value as RollingConfigData['function'])}
        >
            {#each functions as fn}
                <option value={fn.value}>{fn.label}</option>
            {/each}
        </select>
    </div>

    <div class="field">
        <label for="newColumn">Output Column (optional)</label>
        <input
            id="newColumn"
            type="text"
            placeholder="Auto-generated if empty"
            value={config.newColumn ?? ''}
            onchange={(e) => updateConfig('newColumn', e.currentTarget.value || undefined)}
        />
    </div>
</div>

<style>
    .config-panel {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-3);
    }

    .field {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-1);
    }

    label {
        font-size: var(--text-sm);
        font-weight: 500;
        color: var(--text-secondary);
    }

    select, input {
        padding: var(--spacing-2);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        background: var(--bg-primary);
        color: var(--text-primary);
    }
</style>
```

### Export Component

Add to `frontend/src/lib/components/operations/index.ts`:

```typescript
export { default as RollingConfig } from './RollingConfig.svelte';
```

## Step 5: Register Operation

### Step Library

Add to the step library configuration:

```typescript
// In pipeline editor or step library
const operations = [
    // ... existing operations ...
    {
        type: 'rolling',
        name: 'Rolling Window',
        category: 'transformation',
        icon: 'chart-line',
        description: 'Calculate rolling window statistics'
    }
];
```

### Config Component Mapping

```typescript
// In operation config panel
const configComponents: Record<string, Component> = {
    filter: FilterConfig,
    select: SelectConfig,
    // ... existing mappings ...
    rolling: RollingConfig
};
```

### Default Config

```typescript
// Default configuration for new rolling steps
const defaultConfigs: Record<string, unknown> = {
    // ... existing defaults ...
    rolling: {
        column: '',
        windowSize: 3,
        function: 'mean',
        newColumn: undefined
    }
};
```

## Step 6: Add Tests

### Backend Test

`backend/tests/test_rolling.py`:

```python
import pytest
import polars as pl
import tempfile
from pathlib import Path

from modules.compute.engine import PolarsComputeEngine
from modules.compute.step_converter import convert_rolling_config

@pytest.fixture
def sample_data():
    """Create sample time series data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("date,value\n")
        for i in range(10):
            f.write(f"2024-01-{i+1:02d},{i*10}\n")
        yield f.name
    Path(f.name).unlink()

def test_convert_rolling_config():
    """Test rolling config conversion."""
    frontend_config = {
        'column': 'value',
        'windowSize': 3,
        'function': 'mean'
    }

    result = convert_rolling_config(frontend_config)

    assert result['column'] == 'value'
    assert result['window_size'] == 3
    assert result['function'] == 'mean'

def test_rolling_mean(sample_data):
    """Test rolling mean operation."""
    engine = PolarsComputeEngine("test")

    datasource_config = {
        "source_type": "file",
        "file_path": sample_data,
        "file_type": "csv"
    }

    pipeline_steps = [{
        "id": "step-1",
        "type": "rolling",
        "config": {
            "column": "value",
            "windowSize": 3,
            "function": "mean"
        },
        "depends_on": []
    }]

    engine.start()
    job_id = engine.execute(datasource_config, pipeline_steps)

    result = None
    for _ in range(10):
        result = engine.get_result(timeout=1.0)
        if result and result.get("status") == "completed":
            break

    engine.shutdown()

    assert result is not None
    assert result["status"] == "completed"
    assert "value_rolling_mean" in result["data"]["schema"]
```

### Frontend Test

`frontend/src/lib/components/operations/RollingConfig.test.ts`:

```typescript
import { render, fireEvent, screen } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import RollingConfig from './RollingConfig.svelte';

describe('RollingConfig', () => {
    const defaultProps = {
        config: {
            column: '',
            windowSize: 3,
            function: 'mean' as const
        },
        schema: {
            columns: [
                { name: 'value', dtype: 'Float64', nullable: false },
                { name: 'name', dtype: 'String', nullable: true }
            ],
            row_count: 100
        },
        onConfigChange: vi.fn()
    };

    it('renders column selector with numeric columns only', () => {
        render(RollingConfig, { props: defaultProps });

        const select = screen.getByLabelText('Column');
        expect(select).toBeInTheDocument();

        // Should show value (Float64) but not name (String)
        expect(screen.getByText('value (Float64)')).toBeInTheDocument();
        expect(screen.queryByText('name (String)')).not.toBeInTheDocument();
    });

    it('calls onConfigChange when window size changes', async () => {
        const onConfigChange = vi.fn();
        render(RollingConfig, {
            props: { ...defaultProps, onConfigChange }
        });

        const input = screen.getByLabelText('Window Size');
        await fireEvent.change(input, { target: { value: '5' } });

        expect(onConfigChange).toHaveBeenCalledWith(
            expect.objectContaining({ windowSize: 5 })
        );
    });
});
```

## Step 7: Update Documentation

### Operations Reference

Add to `docs/reference/polars-operations.md`:

```markdown
### rolling

Calculate rolling window statistics.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `column` | string | Yes | - | Column to compute rolling stats |
| `window_size` | int | No | 3 | Window size |
| `function` | string | No | `mean` | Rolling function |
| `new_column` | string | No | auto | Output column name |

**Functions:**
| Function | Description |
|----------|-------------|
| `mean` | Rolling average |
| `sum` | Rolling sum |
| `std` | Rolling standard deviation |
| `min` | Rolling minimum |
| `max` | Rolling maximum |

**Example:**
```json
{
    "operation": "rolling",
    "params": {
        "column": "price",
        "window_size": 7,
        "function": "mean",
        "new_column": "price_7day_avg"
    }
}
```
```

## Checklist

- [ ] Backend: Add operation to `engine.py` `_apply_step()`
- [ ] Backend: Add converter to `step_converter.py`
- [ ] Backend: Register converter in `get_converters()`
- [ ] Frontend: Add TypeScript interface to `operation-config.ts`
- [ ] Frontend: Update `OperationConfig` union type
- [ ] Frontend: Create configuration component
- [ ] Frontend: Export component from `index.ts`
- [ ] Frontend: Add to step library
- [ ] Frontend: Add config component mapping
- [ ] Frontend: Add default configuration
- [ ] Tests: Add backend unit tests
- [ ] Tests: Add frontend component tests
- [ ] Docs: Update operations reference

## See Also

- [Polars Operations](../reference/polars-operations.md) - Existing operations
- [Compute Engine](../backend/compute-engine/README.md) - Engine architecture
- [Testing Guide](./testing.md) - Testing approach
