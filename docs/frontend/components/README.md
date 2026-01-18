# Components

Documentation for the Svelte component library.

## Overview

Components are organized by feature area. All components use Svelte 5 runes syntax with TypeScript.

## Component Structure

```
lib/components/
├── pipeline/              # Pipeline editor components
│   ├── PipelineCanvas.svelte
│   ├── StepNode.svelte
│   ├── StepConfig.svelte
│   ├── StepLibrary.svelte
│   ├── DatasourceNode.svelte
│   ├── ConnectionLine.svelte
│   └── index.ts
│
├── operations/            # Operation config forms
│   ├── FilterConfig.svelte
│   ├── SelectConfig.svelte
│   ├── GroupByConfig.svelte
│   ├── SortConfig.svelte
│   ├── ... (20+ configs)
│   └── index.ts
│
├── viewers/               # Data display components
│   ├── DataTable.svelte
│   ├── InlineDataTable.svelte
│   ├── SchemaViewer.svelte
│   ├── StatsPanel.svelte
│   └── index.ts
│
├── gallery/               # Gallery/home components
│   ├── GalleryGrid.svelte
│   ├── AnalysisCard.svelte
│   ├── AnalysisFilters.svelte
│   ├── EmptyState.svelte
│   └── index.ts
│
└── common/                # Shared UI components
    ├── ConfirmDialog.svelte
    └── index.ts
```

## Component Conventions

### Svelte 5 Syntax

```svelte
<script lang="ts">
    // Props using $props()
    interface Props {
        title: string;
        items: Item[];
        onSelect?: (item: Item) => void;
    }
    let { title, items, onSelect }: Props = $props();

    // Local state using $state()
    let selected = $state<Item | null>(null);
    let expanded = $state(false);

    // Derived values using $derived()
    let count = $derived(items.length);
    let filtered = $derived.by(() => {
        return items.filter(item => item.active);
    });

    // Side effects using $effect()
    $effect(() => {
        console.log(`Selected: ${selected?.name}`);
    });

    // Event handlers
    function handleClick(item: Item) {
        selected = item;
        onSelect?.(item);
    }
</script>

<div class="component">
    <h2>{title} ({count})</h2>
    {#each filtered as item}
        <button onclick={() => handleClick(item)}>
            {item.name}
        </button>
    {/each}
</div>

<style>
    .component {
        /* Scoped styles */
    }
</style>
```

### File Naming

- Components: `PascalCase.svelte`
- Tests: `ComponentName.test.ts`
- Index exports: `index.ts`

---

## Pipeline Components

### PipelineCanvas

Main canvas for the visual pipeline builder.

```svelte
<script lang="ts">
    interface Props {
        steps: PipelineStep[];
        onStepSelect: (stepId: string) => void;
        onStepAdd: (step: PipelineStep, parentId: string | null) => void;
    }
</script>
```

**Features**:
- Renders pipeline as connected nodes
- Handles drag-and-drop
- Manages step connections
- Zoom and pan support

### StepNode

Individual step in the pipeline.

```svelte
<script lang="ts">
    interface Props {
        step: PipelineStep;
        selected: boolean;
        schema: Schema | null;
        onSelect: () => void;
        onDelete: () => void;
    }
</script>
```

**Displays**:
- Step type icon
- Step name
- Input/output schema
- Delete button

### StepConfig

Configuration panel for selected step.

```svelte
<script lang="ts">
    interface Props {
        step: PipelineStep;
        schema: Schema;
        onUpdate: (config: StepConfig) => void;
    }
</script>
```

**Dynamically loads** the appropriate config component based on step type.

### StepLibrary

Draggable list of available operations.

```svelte
<script lang="ts">
    interface Props {
        onDragStart: (operation: OperationType) => void;
    }
</script>
```

**Categories**:
- Selection (select, drop, rename)
- Filtering (filter, limit, sample)
- Aggregation (groupby, value_counts)
- Reshaping (pivot, unpivot, explode)
- Transform (sort, deduplicate, fill_null)
- String operations
- Time series

---

## Operation Configs

Each operation has a dedicated config component.

### FilterConfig

```svelte
<script lang="ts">
    interface Props {
        config: FilterConfig;
        schema: Schema;
        onUpdate: (config: FilterConfig) => void;
    }
</script>
```

**Fields**:
- Conditions list (column, operator, value)
- Logic selector (AND/OR)
- Add/remove condition buttons

### SelectConfig

```svelte
<script lang="ts">
    interface Props {
        config: SelectConfig;
        schema: Schema;
        onUpdate: (config: SelectConfig) => void;
    }
</script>
```

**Fields**:
- Multi-select column picker
- Select all / clear buttons

### GroupByConfig

```svelte
<script lang="ts">
    interface Props {
        config: GroupByConfig;
        schema: Schema;
        onUpdate: (config: GroupByConfig) => void;
    }
</script>
```

**Fields**:
- Group-by column selector
- Aggregation list (column, function)
- Add aggregation button

### Full Operation List

| Component | Operation | Description |
|-----------|-----------|-------------|
| FilterConfig | filter | Row filtering |
| SelectConfig | select | Column selection |
| DropConfig | drop | Column removal |
| RenameConfig | rename | Column renaming |
| SortConfig | sort | Row sorting |
| GroupByConfig | groupby | Aggregation |
| LimitConfig | limit | Row limit |
| SampleConfig | sample | Random sample |
| TopKConfig | topk | Top K rows |
| PivotConfig | pivot | Wide format |
| UnpivotConfig | unpivot | Long format |
| ExplodeConfig | explode | List expansion |
| JoinConfig | join | Self-join |
| FillNullConfig | fill_null | Null handling |
| DeduplicateConfig | deduplicate | Remove duplicates |
| StringMethodsConfig | string_transform | String ops |
| TimeSeriesConfig | timeseries | Date/time ops |
| ValueCountsConfig | value_counts | Frequency count |
| NullCountConfig | null_count | Null statistics |
| ExpressionConfig | with_columns | Add columns |
| ViewConfig | view | Preview checkpoint |

---

## Viewer Components

### DataTable

Full-featured data table with pagination.

```svelte
<script lang="ts">
    interface Props {
        data: Record<string, unknown>[];
        schema: Schema;
        page?: number;
        pageSize?: number;
        onPageChange?: (page: number) => void;
    }
</script>
```

**Features**:
- Column headers with types
- Sortable columns
- Pagination controls
- Row count display

### InlineDataTable

Compact table for inline previews.

```svelte
<script lang="ts">
    interface Props {
        data: Record<string, unknown>[];
        maxRows?: number;
    }
</script>
```

### SchemaViewer

Displays column names and data types.

```svelte
<script lang="ts">
    interface Props {
        schema: Schema;
        compact?: boolean;
    }
</script>
```

**Shows**:
- Column name
- Data type (with color coding)
- Nullable indicator

### StatsPanel

Statistical summary of results.

```svelte
<script lang="ts">
    interface Props {
        rowCount: number;
        columnCount: number;
        executionTime?: number;
    }
</script>
```

---

## Gallery Components

### GalleryGrid

Grid layout for analysis cards.

```svelte
<script lang="ts">
    interface Props {
        analyses: Analysis[];
        onSelect: (id: string) => void;
        onDelete: (id: string) => void;
    }
</script>
```

### AnalysisCard

Card displaying analysis summary.

```svelte
<script lang="ts">
    interface Props {
        analysis: Analysis;
        onSelect: () => void;
        onDelete: () => void;
    }
</script>
```

**Displays**:
- Name
- Thumbnail (if available)
- Created/updated dates
- Row/column counts
- Action buttons

### AnalysisFilters

Filter controls for the gallery.

```svelte
<script lang="ts">
    interface Props {
        onSearch: (query: string) => void;
        onSort: (field: SortField) => void;
    }
</script>
```

### EmptyState

Displayed when no analyses exist.

```svelte
<script lang="ts">
    interface Props {
        onCreate: () => void;
    }
</script>
```

---

## Common Components

### ConfirmDialog

Modal confirmation dialog.

```svelte
<script lang="ts">
    interface Props {
        open: boolean;
        title: string;
        message: string;
        confirmText?: string;
        cancelText?: string;
        onConfirm: () => void;
        onCancel: () => void;
    }
</script>
```

**Usage**:

```svelte
<ConfirmDialog
    open={showDialog}
    title="Delete Analysis"
    message="Are you sure you want to delete this analysis?"
    confirmText="Delete"
    onConfirm={handleDelete}
    onCancel={() => showDialog = false}
/>
```

---

## Testing

Components have co-located tests:

```
components/
├── gallery/
│   ├── AnalysisCard.svelte
│   └── AnalysisCard.test.ts
└── operations/
    ├── FilterConfig.svelte
    └── FilterConfig.test.ts
```

### Test Example

```typescript
// AnalysisCard.test.ts
import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import AnalysisCard from './AnalysisCard.svelte';

describe('AnalysisCard', () => {
    const mockAnalysis = {
        id: '123',
        name: 'Test Analysis',
        created_at: new Date().toISOString()
    };

    it('renders analysis name', () => {
        const { getByText } = render(AnalysisCard, {
            props: { analysis: mockAnalysis }
        });
        expect(getByText('Test Analysis')).toBeTruthy();
    });

    it('calls onSelect when clicked', async () => {
        const onSelect = vi.fn();
        const { getByRole } = render(AnalysisCard, {
            props: { analysis: mockAnalysis, onSelect }
        });

        await fireEvent.click(getByRole('button'));
        expect(onSelect).toHaveBeenCalled();
    });
});
```

## See Also

- [Styling](../styling.md) - Design system
- [State Management](../state-management/README.md) - Store integration
- [Pipeline Builder](../../guides/building-pipelines.md) - User guide
