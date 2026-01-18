# Operations Components

Configuration components for pipeline operations.

## Overview

Each Polars operation has a corresponding Svelte component for configuring its parameters. These components receive the current schema and emit configuration changes.

## Component Pattern

All operation config components follow this pattern:

```svelte
<script lang="ts">
    import type { Schema } from '$lib/types/schema';

    interface Props {
        schema: Schema;
        config?: ConfigType;
    }

    let { schema, config = $bindable(defaultConfig) }: Props = $props();
</script>
```

### Key Features

- **Two-way binding**: `$bindable()` for config prop
- **Schema awareness**: Access to column names and types
- **Safe accessors**: Handle empty/malformed config
- **Validation**: Prevent invalid configurations

---

## Filter Operations

### FilterConfig

**Location:** `frontend/src/lib/components/operations/FilterConfig.svelte`

Configure row filtering conditions.

#### Config Structure

```typescript
interface FilterConfigData {
    conditions: FilterCondition[];
    logic: 'AND' | 'OR';
}

interface FilterCondition {
    column: string;
    operator: string;
    value: string;
}
```

#### Features

- **Multiple conditions**: Add/remove condition rows
- **Logic selector**: AND/OR combination
- **Dynamic input type**: Number/text based on column type
- **Operator selection**: =, !=, >, <, >=, <=, contains

#### Supported Operators

| Operator | Description | Applicable Types |
|----------|-------------|------------------|
| `=` | Equals | All |
| `!=` | Not equals | All |
| `>` | Greater than | Numeric, Date |
| `<` | Less than | Numeric, Date |
| `>=` | Greater or equal | Numeric, Date |
| `<=` | Less or equal | Numeric, Date |
| `contains` | String contains | String |

---

### LimitConfig

**Location:** `frontend/src/lib/components/operations/LimitConfig.svelte`

Configure row limit.

```typescript
interface LimitConfigData {
    n: number;
}
```

---

### SampleConfig

**Location:** `frontend/src/lib/components/operations/SampleConfig.svelte`

Configure random sampling.

```typescript
interface SampleConfigData {
    n?: number;
    fraction?: number;
    shuffle?: boolean;
    seed?: number;
}
```

---

### TopKConfig

**Location:** `frontend/src/lib/components/operations/TopKConfig.svelte`

Configure top K rows selection.

```typescript
interface TopKConfigData {
    column: string;
    k: number;
    descending: boolean;
}
```

---

## Selection Operations

### SelectConfig

**Location:** `frontend/src/lib/components/operations/SelectConfig.svelte`

Configure column selection.

```typescript
interface SelectConfigData {
    columns: string[];
}
```

#### Features

- **Multi-select**: Checkbox list of columns
- **Select all/none**: Bulk selection
- **Column info**: Shows data type

---

### DropConfig

**Location:** `frontend/src/lib/components/operations/DropConfig.svelte`

Configure columns to remove.

```typescript
interface DropConfigData {
    columns: string[];
}
```

---

### RenameConfig

**Location:** `frontend/src/lib/components/operations/RenameConfig.svelte`

Configure column renaming.

```typescript
interface RenameConfigData {
    column_mapping: Record<string, string>;
}
```

#### Features

- **Dynamic rows**: Add multiple rename mappings
- **Validation**: Prevent duplicate names

---

## Aggregation Operations

### GroupByConfig

**Location:** `frontend/src/lib/components/operations/GroupByConfig.svelte`

Configure grouping and aggregations.

```typescript
interface GroupByConfigData {
    groupBy: string[];
    aggregations: Aggregation[];
}

interface Aggregation {
    column: string;
    function: string;
    alias: string;
}
```

#### Features

- **Group by columns**: Multi-select
- **Aggregation list**: Add multiple aggregations
- **Function selection**: sum, mean, count, min, max
- **Auto-alias**: Generates `{column}_{function}`

---

### ValueCountsConfig

**Location:** `frontend/src/lib/components/operations/ValueCountsConfig.svelte`

Configure value frequency counting.

```typescript
interface ValueCountsConfigData {
    column: string;
    normalize?: boolean;
    sort?: boolean;
}
```

---

### NullCountConfig

**Location:** `frontend/src/lib/components/operations/NullCountConfig.svelte`

No configuration required (counts nulls for all columns).

```typescript
interface NullCountConfigData extends Record<string, never> {}
```

---

## Transformation Operations

### SortConfig

**Location:** `frontend/src/lib/components/operations/SortConfig.svelte`

Configure row sorting.

```typescript
type SortConfigData = SortRule[];

interface SortRule {
    column: string;
    descending: boolean;
}
```

#### Features

- **Multiple sort keys**: Priority-ordered list
- **Direction toggle**: Ascending/descending per column
- **Reorder**: Drag to change priority

---

### DeduplicateConfig

**Location:** `frontend/src/lib/components/operations/DeduplicateConfig.svelte`

Configure duplicate removal.

```typescript
interface DeduplicateConfigData {
    subset: string[] | null;
    keep: string;
}
```

#### Keep Options

| Value | Description |
|-------|-------------|
| `first` | Keep first occurrence |
| `last` | Keep last occurrence |
| `none` | Remove all duplicates |

---

### FillNullConfig

**Location:** `frontend/src/lib/components/operations/FillNullConfig.svelte`

Configure null value handling.

```typescript
interface FillNullConfigData {
    strategy: string;
    columns: string[] | null;
    value?: string | number;
}
```

#### Strategies

| Strategy | Description |
|----------|-------------|
| `literal` | Fill with constant value |
| `forward` | Forward fill (last valid) |
| `backward` | Backward fill (next valid) |
| `mean` | Fill with column mean |
| `median` | Fill with column median |
| `drop_rows` | Remove rows with nulls |

---

### ExpressionConfig

**Location:** `frontend/src/lib/components/operations/ExpressionConfig.svelte`

Configure computed columns.

```typescript
interface ExpressionConfigData {
    expression: string;
    column_name: string;
}
```

---

## Reshaping Operations

### PivotConfig

**Location:** `frontend/src/lib/components/operations/PivotConfig.svelte`

Configure wide format transformation.

```typescript
interface PivotConfigData {
    index: string[];
    columns: string;
    values: string;
    aggregate_function: string;
}
```

---

### UnpivotConfig

**Location:** `frontend/src/lib/components/operations/UnpivotConfig.svelte`

Configure long format transformation.

```typescript
interface UnpivotConfigData {
    index?: string[];
    on?: string[];
    variable_name?: string;
    value_name?: string;
}
```

---

### ExplodeConfig

**Location:** `frontend/src/lib/components/operations/ExplodeConfig.svelte`

Configure list column explosion.

```typescript
interface ExplodeConfigData {
    columns: string[];
}
```

---

## String Operations

### StringMethodsConfig

**Location:** `frontend/src/lib/components/operations/StringMethodsConfig.svelte`

Configure string transformations.

```typescript
interface StringMethodsConfigData {
    column: string;
    method: string;
    new_column: string;
    start?: number;
    end?: number | null;
    pattern?: string;
    replacement?: string;
    group_index?: number;
    delimiter?: string;
    index?: number;
}
```

#### Methods

| Method | Description | Extra Params |
|--------|-------------|--------------|
| `uppercase` | To uppercase | - |
| `lowercase` | To lowercase | - |
| `title` | To title case | - |
| `strip` | Trim whitespace | - |
| `length` | Get length | - |
| `slice` | Substring | `start`, `end` |
| `replace` | Replace pattern | `pattern`, `replacement` |
| `extract` | Regex extract | `pattern`, `group_index` |
| `split` | Split and get | `delimiter`, `index` |

---

## Time Series Operations

### TimeSeriesConfig

**Location:** `frontend/src/lib/components/operations/TimeSeriesConfig.svelte`

Configure datetime operations.

```typescript
interface TimeSeriesConfigData {
    column: string;
    operation_type: string;
    new_column: string;
    component?: string;
    value?: number;
    unit?: string;
    column2?: string;
}
```

#### Operation Types

| Type | Description | Extra Params |
|------|-------------|--------------|
| `extract` | Get date part | `component` |
| `add` | Add duration | `value`, `unit` |
| `subtract` | Subtract duration | `value`, `unit` |
| `diff` | Difference | `column2` |

---

## Special Operations

### ViewConfig

**Location:** `frontend/src/lib/components/operations/ViewConfig.svelte`

Configure data preview.

```typescript
interface ViewConfigData {
    rowLimit: number;
}
```

---

### JoinConfig

**Location:** `frontend/src/lib/components/operations/JoinConfig.svelte`

Configure table joins (self-join only currently).

```typescript
interface JoinConfigData {
    how: 'inner' | 'left' | 'right' | 'outer';
    left_on: string[];
    right_on: string[];
}
```

---

## Creating New Config Components

### Template

```svelte
<script lang="ts">
    import type { Schema } from '$lib/types/schema';

    interface MyConfigData {
        param1: string;
        param2: number;
    }

    interface Props {
        schema: Schema;
        config?: MyConfigData;
    }

    let {
        schema,
        config = $bindable({ param1: '', param2: 0 })
    }: Props = $props();

    // Safe accessors for potentially malformed config
    let safeParam1 = $derived(config?.param1 ?? '');
    let safeParam2 = $derived(config?.param2 ?? 0);

    // Initialize empty config
    $effect(() => {
        if (!config || typeof config !== 'object') {
            config = { param1: '', param2: 0 };
        }
    });
</script>

<div class="my-config">
    <h3>My Operation</h3>

    <div class="field">
        <label for="param1">Parameter 1</label>
        <select id="param1" bind:value={config.param1}>
            <option value="">Select...</option>
            {#each schema.columns as col}
                <option value={col.name}>{col.name}</option>
            {/each}
        </select>
    </div>

    <div class="field">
        <label for="param2">Parameter 2</label>
        <input
            id="param2"
            type="number"
            bind:value={config.param2}
        />
    </div>
</div>

<style>
    .my-config {
        padding: 1rem;
        border: 1px solid var(--panel-border);
        border-radius: var(--radius-md);
        background-color: var(--panel-bg);
    }

    .field {
        margin-bottom: 1rem;
    }

    label {
        display: block;
        margin-bottom: 0.25rem;
        color: var(--fg-secondary);
    }

    select, input {
        width: 100%;
        padding: 0.5rem;
        border: 1px solid var(--form-control-border);
        border-radius: var(--radius-sm);
        background-color: var(--form-control-bg);
        color: var(--fg-primary);
    }
</style>
```

---

## See Also

- [Pipeline Components](../pipeline/README.md) - Canvas and nodes
- [Type Definitions](../../../reference/type-definitions.md) - Config types
- [Polars Operations](../../../reference/polars-operations.md) - Operation reference
- [Adding Operations](../../../guides/adding-operations.md) - Extending the engine
