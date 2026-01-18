# Viewer Components

Components for displaying data and schema information.

## Overview

Viewer components present data results, schema information, and statistics to users. They are used in the results panel and inline within pipeline steps.

## Components

### DataTable

**Location:** `frontend/src/lib/components/viewers/DataTable.svelte`

Full-featured data table with sorting and pagination.

#### Props

```typescript
interface Props {
    columns: string[];
    data: Record<string, unknown>[];
    loading?: boolean;
    onSort?: (column: string, direction: 'asc' | 'desc') => void;
}
```

#### Features

- **Sortable columns**: Click headers to sort
- **Loading state**: Spinner overlay
- **Empty state**: "No data available" message
- **Row count**: Footer with total rows
- **Sticky header**: Fixed during scroll
- **Alternating rows**: Zebra striping
- **Hover highlight**: Row hover effect
- **Value formatting**: Locale-aware numbers, null handling

#### Usage

```svelte
<DataTable
    columns={['id', 'name', 'amount']}
    data={results}
    loading={isLoading}
    onSort={(col, dir) => handleSort(col, dir)}
/>
```

#### Sorting Logic

```typescript
let sortedData = $derived(() => {
    if (!sortColumn) return data;

    return [...data].sort((a, b) => {
        const aVal = a[sortColumn];
        const bVal = b[sortColumn];

        // Nulls sort last
        if (aVal === null || aVal === undefined) return 1;
        if (bVal === null || bVal === undefined) return -1;

        // Numeric comparison
        if (typeof aVal === 'number' && typeof bVal === 'number') {
            return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
        }

        // String comparison
        const comparison = String(aVal).localeCompare(String(bVal));
        return sortDirection === 'asc' ? comparison : -comparison;
    });
});
```

#### Value Formatting

```typescript
function formatValue(value: TableCellValue): string {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'number') return value.toLocaleString();
    if (typeof value === 'boolean') return value ? 'true' : 'false';
    return String(value);
}
```

---

### InlineDataTable

**Location:** `frontend/src/lib/components/viewers/InlineDataTable.svelte`

Compact data preview for inline display within pipeline nodes.

#### Props

```typescript
interface Props {
    datasourceId: string;
    pipeline: PipelineStep[];
    stepId: string;
    rowLimit?: number;
}
```

#### Features

- **Auto-fetch**: Fetches data when visible
- **Row limit**: Configurable preview size
- **Compact styling**: Fits within step nodes
- **Error handling**: Shows error states

#### Usage

```svelte
<!-- Inside StepNode for view operations -->
{#if step.type === 'view'}
    <InlineDataTable
        {datasourceId}
        pipeline={allSteps}
        stepId={step.id}
        rowLimit={100}
    />
{/if}
```

---

### SchemaViewer

**Location:** `frontend/src/lib/components/viewers/SchemaViewer.svelte`

Display column schema information.

#### Props

```typescript
interface Props {
    schema: SchemaInfo | null;
    loading?: boolean;
}
```

#### Features

- **Column list**: Name and data type
- **Row count**: Total rows if available
- **Type badges**: Color-coded by type
- **Loading state**: Skeleton display
- **Null indicator**: Shows nullable status

#### Type Color Coding

```css
/* Numeric types */
.type-numeric { color: var(--type-numeric); }

/* String types */
.type-string { color: var(--type-string); }

/* Boolean */
.type-boolean { color: var(--type-boolean); }

/* Temporal */
.type-temporal { color: var(--type-temporal); }

/* Complex */
.type-complex { color: var(--type-complex); }
```

#### Usage

```svelte
<SchemaViewer
    schema={currentSchema}
    loading={isLoadingSchema}
/>
```

---

### StatsPanel

**Location:** `frontend/src/lib/components/viewers/StatsPanel.svelte`

Display execution statistics and metadata.

#### Props

```typescript
interface Props {
    stats: {
        rowCount: number;
        columnCount: number;
        executionTime?: number;
        memoryUsage?: number;
    } | null;
}
```

#### Features

- **Key metrics**: Row/column counts
- **Performance**: Execution time
- **Memory**: Memory usage if available
- **Formatted values**: Human-readable numbers

#### Usage

```svelte
<StatsPanel
    stats={{
        rowCount: 10000,
        columnCount: 15,
        executionTime: 1.23
    }}
/>
```

---

## Styling

### Table Styles

```css
.data-table-container {
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    border-radius: var(--radius-md);
    overflow: hidden;
}

.table-wrapper {
    overflow-x: auto;
    max-height: 600px;
    overflow-y: auto;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
}

thead {
    position: sticky;
    top: 0;
    background: var(--table-header-bg);
    z-index: 10;
}

th {
    padding: 0;
    border-bottom: 2px solid var(--table-border);
    font-weight: 600;
    text-align: left;
}

tbody tr:nth-child(even) {
    background: var(--table-row-alt);
}

tbody tr:hover {
    background: var(--table-row-hover);
}

td {
    padding: 0.75rem 1rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 300px;
}
```

### Loading States

```css
.loading-overlay {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem;
    gap: 1rem;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--border-primary);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
```

---

## Integration

### With Compute Store

```typescript
import { computeStore } from '$lib/stores/compute.svelte';

// Get current job results
const results = $derived(computeStore.currentResult);
const isLoading = $derived(computeStore.currentJob?.status === 'running');
```

### With API Client

```typescript
import { executeCompute } from '$lib/api/compute';

async function runPipeline() {
    const result = await executeCompute(analysisId, tabId);
    if (result.isOk()) {
        // Results available via store
    }
}
```

---

## Accessibility

- **Sortable columns**: Button role with aria-label
- **Loading announcements**: aria-live region
- **Table semantics**: Proper `<table>`, `<thead>`, `<tbody>`
- **Keyboard navigation**: Tab through headers
- **Focus indicators**: Visible focus states

---

## Performance Considerations

1. **Virtual scrolling**: Consider for large datasets
2. **Debounced sorting**: Prevent rapid re-renders
3. **Memoized formatting**: Cache formatted values
4. **Lazy loading**: Load data on demand

---

## See Also

- [Pipeline Components](../pipeline/README.md) - Pipeline editor
- [State Management](../../state-management/README.md) - Compute store
- [API Client](../../api-client/README.md) - Data fetching
