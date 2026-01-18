# Pipeline Components

Components for the visual pipeline builder.

## Overview

The pipeline components form the core of the visual DAG builder, enabling users to create data transformation pipelines through drag-and-drop interactions.

## Components

### PipelineCanvas

**Location:** `frontend/src/lib/components/pipeline/PipelineCanvas.svelte`

The main canvas area where pipeline steps are displayed and manipulated.

#### Props

```typescript
interface Props {
    steps: PipelineStep[];
    datasourceId?: string;
    datasource?: DataSource | null;
    tabName?: string;
    onStepClick: (id: string) => void;
    onStepDelete: (id: string) => void;
    onInsertStep: (type: string, target: DropTarget) => void;
    onMoveStep: (stepId: string, target: DropTarget) => void;
    onChangeDatasource?: () => void;
    onRenameTab?: (name: string) => void;
}
```

#### Features

- **Empty state**: Shows instructions when no steps exist
- **Drop zones**: Visual indicators for valid drop targets
- **Drag validation**: Prevents invalid step placements
- **Connection lines**: Visual links between steps

#### Usage

```svelte
<PipelineCanvas
    {steps}
    {datasourceId}
    {datasource}
    onStepClick={(id) => selectStep(id)}
    onStepDelete={(id) => deleteStep(id)}
    onInsertStep={(type, target) => insertStep(type, target)}
    onMoveStep={(stepId, target) => moveStep(stepId, target)}
/>
```

#### Drop Target Logic

The canvas calculates valid drop positions based on:
- Current step dependencies
- Drag operation type (insert vs reorder)
- Step position constraints

```typescript
interface DropTarget {
    index: number;        // Position in steps array
    parentId: string | null;  // Previous step ID
    nextId: string | null;    // Next step ID
}
```

---

### StepNode

**Location:** `frontend/src/lib/components/pipeline/StepNode.svelte`

Individual step representation in the pipeline.

#### Props

```typescript
interface Props {
    step: PipelineStep;
    index: number;
    datasourceId?: string;
    allSteps?: PipelineStep[];
    onEdit: (id: string) => void;
    onDelete: (id: string) => void;
}
```

#### Features

- **Type display**: Shows operation type with monospace font
- **Config summary**: Brief description of step configuration
- **Draggable**: Native HTML5 drag support
- **Actions**: Edit and delete buttons
- **View preview**: Inline data preview for `view` steps

#### Configuration Summaries

The component generates human-readable summaries:

| Type | Summary Example |
|------|-----------------|
| `filter` | "2 conditions" |
| `select` | "5 columns" |
| `groupby` | "2 keys, 3 agg" |
| `sort` | "2 columns" |
| other | "click to configure" |

#### Drag Events

```typescript
function handleDragStart(event: DragEvent) {
    isDragging = true;
    event.dataTransfer.setData('application/x-pipeline-step', step.id);
    event.dataTransfer.effectAllowed = 'move';
    drag.startMove(step.id, step.type);
}
```

---

### StepLibrary

**Location:** `frontend/src/lib/components/pipeline/StepLibrary.svelte`

Sidebar panel containing available operations.

#### Features

- **Categorized operations**: Grouped by function
- **Draggable items**: Drag to canvas to add
- **Search/filter**: Find operations quickly

#### Categories
 
| Category | Operations |
|----------|------------|
| Filter | filter, limit, sample, topk |
| Select | select, drop, rename |
| Aggregate | groupby, value_counts, null_count |
| Transform | sort, deduplicate, fill_null, with_columns |
| Reshape | pivot, unpivot, explode |
| String | string_transform |
| Time | timeseries |
| Export | export |
| View | view |


#### Drag Initialization

```typescript
function handleDragStart(event: DragEvent, type: string) {
    event.dataTransfer.setData('text/plain', type);
    event.dataTransfer.effectAllowed = 'copy';
    drag.startInsert(type);
}
```

---

### DatasourceNode

**Location:** `frontend/src/lib/components/pipeline/DatasourceNode.svelte`

The root node displaying the data source.

#### Props

```typescript
interface Props {
    datasource: DataSource;
    tabName?: string;
    onChangeDatasource?: () => void;
    onRenameTab?: (name: string) => void;
}
```

#### Features

- **Non-draggable**: Fixed at pipeline start
- **Name editing**: Inline tab renaming
- **Change button**: Switch data source
- **Schema preview**: Shows column count

---

### ConnectionLine

**Location:** `frontend/src/lib/components/pipeline/ConnectionLine.svelte`

SVG connector between steps.

#### Props

```typescript
interface Props {
    fromStepIndex: number;
    toStepIndex: number;
    totalSteps: number;
    highlighted?: boolean;
}
```

#### Features

- **Animated dash**: Flow direction indicator
- **Highlight state**: Active during drag operations
- **Responsive**: Adjusts to step positions

---

### StepConfig

**Location:** `frontend/src/lib/components/pipeline/StepConfig.svelte`

Configuration panel for the selected step.

#### Props

```typescript
interface Props {
    step: PipelineStep | null;
    schema: Schema | null;
    onConfigChange: (config: Record<string, unknown>) => void;
}
```

#### Features

- **Dynamic component**: Loads appropriate config component
- **Schema awareness**: Passes column info to configs
- **Debounced save**: Auto-saves with delay

#### Component Mapping

```typescript
const configComponents: Record<string, Component> = {
    filter: FilterConfig,
    select: SelectConfig,
    groupby: GroupByConfig,
    sort: SortConfig,
    rename: RenameConfig,
    drop: DropConfig,
    // ... more mappings
};
```

---

## State Integration

### Drag Store

Pipeline components use a shared drag store:

```typescript
// $lib/stores/drag.svelte.ts
class DragStore {
    active = $state(false);
    type = $state<string | null>(null);
    stepId = $state<string | null>(null);
    target = $state<DropTarget | null>(null);
    valid = $state(false);
    isInsert = $derived(this.active && !this.stepId);
    isReorder = $derived(this.active && !!this.stepId);

    startInsert(type: string) { /* ... */ }
    startMove(stepId: string, type: string) { /* ... */ }
    setTarget(target: DropTarget, valid: boolean) { /* ... */ }
    clearTarget() { /* ... */ }
    end() { /* ... */ }
}
```

### Analysis Store

Steps are managed via the analysis store:

```typescript
// Adding a step
analysisStore.addStep(tabId, {
    id: crypto.randomUUID(),
    type: 'filter',
    config: { conditions: [], logic: 'AND' },
    depends_on: [parentId]
});

// Moving a step
analysisStore.moveStep(tabId, stepId, newIndex, newDependsOn);
```

---

## Styling

### CSS Variables

Pipeline components use these design tokens:

```css
/* Backgrounds */
--bg-primary: #ffffff;
--bg-secondary: #f9fafb;
--bg-tertiary: #f3f4f6;

/* Borders */
--border-primary: #e5e7eb;
--border-tertiary: #9ca3af;

/* Accents */
--accent-primary: #3b82f6;
--accent-soft: rgba(59, 130, 246, 0.1);

/* Spacing */
--space-2: 0.5rem;
--space-4: 1rem;
--space-6: 1.5rem;
```

### Animations

```css
/* Drop slot activation */
.drop-slot.active {
    border-color: var(--fg-primary);
    background-color: var(--bg-tertiary);
}

/* Node drag state */
.step-node.dragging {
    opacity: 0.5;
}

/* Hover lift */
.step-content:hover {
    transform: translateY(-1px);
}
```

---

## Accessibility

- **Keyboard navigation**: Tab through steps
- **ARIA roles**: `role="list"`, `role="listitem"`
- **Focus indicators**: Visible focus states
- **Screen reader labels**: Descriptive button labels

---

## See Also

- [Operations Components](../operations/README.md) - Config components
- [State Management](../../state-management/README.md) - Store patterns
- [Building Pipelines](../../../guides/building-pipelines.md) - User guide
