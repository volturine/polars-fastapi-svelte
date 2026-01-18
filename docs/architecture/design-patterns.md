# Design Patterns

This document describes all architectural and design patterns used in the Polars-FastAPI-Svelte Analysis Platform, with code examples from the actual codebase.

## Table of Contents

1. [Architectural Patterns](#architectural-patterns)
2. [Structural Patterns](#structural-patterns)
3. [Behavioral Patterns](#behavioral-patterns)
4. [Concurrency Patterns](#concurrency-patterns)
5. [Data Patterns](#data-patterns)
6. [Frontend Patterns](#frontend-patterns)

---

## Architectural Patterns

### 1. Monorepo Pattern

**Purpose**: Maintain frontend and backend in a single repository for unified versioning and simplified coordination.

**Implementation**:
```
polars-fastapi-svelte/
├── backend/           # Python FastAPI application
│   ├── pyproject.toml # Python dependencies
│   └── ...
├── frontend/          # SvelteKit application
│   ├── package.json   # Node dependencies
│   └── ...
├── Justfile          # Unified task automation
└── README.md         # Single documentation entry
```

**Benefits**:
- Atomic commits across frontend and backend
- Simplified dependency management
- Unified CI/CD pipeline
- Easier code review for full-stack changes

**Trade-offs**:
- Larger repository size
- Requires polyglot tooling knowledge
- Both apps must be versioned together

---

### 2. Layered Architecture

**Purpose**: Separate concerns into distinct layers with clear responsibilities.

**Backend Layers**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│                      (routes.py)                                │
│  - HTTP request handling                                        │
│  - Request/response serialization                               │
│  - Error mapping to HTTP status codes                           │
├─────────────────────────────────────────────────────────────────┤
│                    BUSINESS LAYER                               │
│                     (service.py)                                │
│  - Business logic and validation                                │
│  - Orchestration of data operations                             │
│  - Transaction management                                       │
├─────────────────────────────────────────────────────────────────┤
│                    DATA ACCESS LAYER                            │
│                     (models.py)                                 │
│  - ORM model definitions                                        │
│  - Database queries                                             │
│  - Data persistence                                             │
├─────────────────────────────────────────────────────────────────┤
│                    CONTRACT LAYER                               │
│                    (schemas.py)                                 │
│  - Request validation schemas                                   │
│  - Response serialization schemas                               │
│  - Data transfer objects                                        │
└─────────────────────────────────────────────────────────────────┘
```

**Example from Analysis Module**:

```python
# routes.py (Presentation Layer)
@router.post('', response_model=AnalysisResponseSchema)
async def create_analysis(
    data: AnalysisCreateSchema,
    session: AsyncSession = Depends(get_db)
) -> AnalysisResponseSchema:
    try:
        return await service.create_analysis(session, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# service.py (Business Layer)
async def create_analysis(
    session: AsyncSession,
    data: AnalysisCreateSchema
) -> AnalysisResponseSchema:
    # Validate datasources exist
    for ds_id in data.datasource_ids:
        result = await session.execute(
            select(DataSource).where(DataSource.id == ds_id)
        )
        if not result.scalar_one_or_none():
            raise ValueError(f'DataSource {ds_id} not found')

    # Create analysis
    analysis = Analysis(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        # ...
    )
    session.add(analysis)
    await session.commit()
    return AnalysisResponseSchema.model_validate(analysis)

# models.py (Data Access Layer)
class Analysis(Base):
    __tablename__ = 'analyses'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # ...

# schemas.py (Contract Layer)
class AnalysisCreateSchema(BaseModel):
    name: str
    description: str | None = None
    datasource_ids: list[str]
    pipeline_steps: list[PipelineStepSchema] = []
```

---

### 3. Modular Architecture

**Purpose**: Organize code by feature/domain rather than by technical layer.

**Implementation**:
```
modules/
├── analysis/          # Analysis feature
│   ├── models.py
│   ├── schemas.py
│   ├── routes.py
│   └── service.py
├── datasource/        # Data source feature
│   ├── models.py
│   ├── schemas.py
│   ├── routes.py
│   └── service.py
├── compute/           # Compute feature
│   ├── engine.py
│   ├── manager.py
│   ├── step_converter.py
│   ├── schemas.py
│   ├── routes.py
│   └── service.py
└── results/           # Results feature
    ├── schemas.py
    ├── routes.py
    └── service.py
```

**Benefits**:
- High cohesion within modules
- Low coupling between modules
- Easy to add new features
- Clear ownership boundaries

---

## Structural Patterns

### 4. Singleton Pattern

**Purpose**: Ensure only one instance of ProcessManager exists across the application.

**Location**: `backend/modules/compute/manager.py`

```python
class ProcessManager:
    """Singleton process manager for compute engines."""

    _instance: 'ProcessManager | None' = None
    _engines: dict[str, EngineInfo]

    def __new__(cls) -> 'ProcessManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engines = {}
        return cls._instance

    def spawn_engine(self, analysis_id: str) -> EngineInfo:
        """Get or create engine for analysis."""
        if analysis_id in self._engines:
            info = self._engines[analysis_id]
            info.touch()  # Update activity
            return info

        # Create new engine
        engine = PolarsComputeEngine(analysis_id)
        engine.start()
        info = EngineInfo(engine)
        self._engines[analysis_id] = info
        return info

# Usage (always returns same instance)
def get_manager() -> ProcessManager:
    return ProcessManager()
```

**Benefits**:
- Centralized engine management
- Shared state across requests
- Resource pooling

---

### 5. Repository Pattern (via Service Layer)

**Purpose**: Abstract data access behind a service interface.

**Location**: `backend/modules/*/service.py`

```python
# datasource/service.py
class DataSourceService:
    """Service layer acts as repository for DataSource."""

    @staticmethod
    async def create_file_datasource(
        session: AsyncSession,
        name: str,
        file_path: str,
        file_type: str
    ) -> DataSource:
        datasource = DataSource(
            id=str(uuid.uuid4()),
            name=name,
            source_type='file',
            config={
                'file_path': file_path,
                'file_type': file_type
            },
            created_at=datetime.now(timezone.utc)
        )
        session.add(datasource)
        await session.commit()
        await session.refresh(datasource)
        return datasource

    @staticmethod
    async def get_datasource(
        session: AsyncSession,
        datasource_id: str
    ) -> DataSource | None:
        result = await session.execute(
            select(DataSource).where(DataSource.id == datasource_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_datasources(
        session: AsyncSession
    ) -> list[DataSource]:
        result = await session.execute(select(DataSource))
        return list(result.scalars().all())
```

**Benefits**:
- Testable (can mock service layer)
- Consistent data access patterns
- Business logic separated from ORM

---

### 6. Dependency Injection Pattern

**Purpose**: Inject dependencies (database sessions, managers) into route handlers.

**Location**: `backend/core/database.py`, `backend/modules/*/routes.py`

```python
# core/database.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides database session."""
    async with AsyncSessionLocal() as session:
        yield session

# modules/compute/manager.py
def get_manager() -> ProcessManager:
    """Dependency that provides process manager."""
    return ProcessManager()

# Usage in routes
@router.post('/execute')
async def execute_analysis(
    data: ComputeExecuteSchema,
    session: AsyncSession = Depends(get_db),      # Injected
    manager: ProcessManager = Depends(get_manager) # Injected
) -> ComputeStatusSchema:
    engine_info = manager.spawn_engine(data.analysis_id)
    # ...
```

**Benefits**:
- Loose coupling
- Easy testing with mock dependencies
- Clear dependency graph

---

## Behavioral Patterns

### 7. Strategy Pattern (via Step Converter)

**Purpose**: Convert different operation types using operation-specific strategies.

**Location**: `backend/modules/compute/step_converter.py`

```python
# Strategy mapping
CONVERTERS: dict[str, Callable] = {
    'filter': convert_filter_config,
    'select': convert_select_config,
    'groupby': convert_groupby_config,
    'join': convert_join_config,
    'pivot': convert_pivot_config,
    # ... more operation converters
}

def convert_step(step: dict) -> dict:
    """Convert frontend step to backend format using appropriate strategy."""
    step_type = step.get('type', '').lower()
    converter = CONVERTERS.get(step_type, convert_passthrough)
    return converter(step)

# Individual strategies
def convert_filter_config(step: dict) -> dict:
    config = step.get('config', {})
    return {
        'name': step['id'],
        'operation': 'filter',
        'params': {
            'conditions': config.get('conditions', []),
            'logic': config.get('logic', 'AND')
        }
    }

def convert_groupby_config(step: dict) -> dict:
    config = step.get('config', {})
    return {
        'name': step['id'],
        'operation': 'group_by',
        'params': {
            'group_by': config.get('groupBy', config.get('group_by', [])),
            'aggregations': config.get('aggregations', [])
        }
    }
```

**Benefits**:
- Easy to add new operation types
- Each converter is independently testable
- Open for extension, closed for modification

---

### 8. Observer Pattern (via Svelte Reactivity)

**Purpose**: Automatically update UI when state changes.

**Location**: `frontend/src/lib/stores/*.svelte.ts`

```typescript
// stores/analysis.svelte.ts
class AnalysisStore {
  // Observable state
  current = $state<Analysis | null>(null);
  tabs = $state<AnalysisTab[]>([]);
  activeTabId = $state<string | null>(null);

  // Derived (computed) state - automatically updates
  activeTab = $derived(
    this.tabs.find(t => t.id === this.activeTabId) ?? null
  );

  pipeline = $derived(
    this.activeTab?.steps ?? []
  );

  // Methods that modify state
  addStep(step: PipelineStep): void {
    if (!this.activeTab) return;

    // Mutation triggers automatic UI updates
    this.activeTab.steps = [...this.activeTab.steps, step];
  }
}

export const analysisStore = new AnalysisStore();

// Component automatically re-renders when state changes
// +page.svelte
<script>
  import { analysisStore } from '$lib/stores';

  // Reactive access
  const pipeline = $derived(analysisStore.pipeline);
</script>

{#each pipeline as step}
  <StepNode {step} />
{/each}
```

**Benefits**:
- Automatic UI synchronization
- No manual subscription management
- Derived state stays consistent

---

### 9. Command Pattern (via Compute Engine)

**Purpose**: Encapsulate execution requests as command objects.

**Location**: `backend/modules/compute/engine.py`

```python
class PolarsComputeEngine:
    def __init__(self, analysis_id: str):
        self.analysis_id = analysis_id
        self.command_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.process: multiprocessing.Process | None = None

    def execute(
        self,
        job_id: str,
        datasource_config: dict,
        pipeline_steps: list[dict]
    ) -> str:
        """Queue execution command."""
        command = {
            'type': 'execute',
            'job_id': job_id,
            'datasource_config': datasource_config,
            'pipeline_steps': pipeline_steps
        }
        self.command_queue.put(command)
        return job_id

    def shutdown(self) -> None:
        """Queue shutdown command."""
        self.command_queue.put({'type': 'shutdown'})

    @staticmethod
    def _run_compute(command_queue, result_queue):
        """Process commands in subprocess."""
        while True:
            command = command_queue.get()

            if command['type'] == 'shutdown':
                break

            if command['type'] == 'execute':
                result = PolarsComputeEngine._execute_pipeline(
                    command['datasource_config'],
                    command['pipeline_steps']
                )
                result_queue.put({
                    'job_id': command['job_id'],
                    **result
                })
```

**Benefits**:
- Decouples request from execution
- Enables queuing and scheduling
- Supports undo/redo (if needed)

---

## Concurrency Patterns

### 10. Producer-Consumer Pattern

**Purpose**: Decouple command production from consumption using queues.

**Location**: `backend/modules/compute/engine.py`

```
┌──────────────────────────────────────────────────────────────────┐
│                   PRODUCER-CONSUMER PATTERN                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PRODUCER (Main Process)                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  engine.execute(job_id, config, steps)                     │  │
│  │      │                                                     │  │
│  │      ▼                                                     │  │
│  │  command_queue.put({type: 'execute', ...})                 │  │
│  └────────────────────────────────────────────────────────────┘  │
│                         │                                        │
│                         ▼                                        │
│              ┌──────────────────────┐                           │
│              │    command_queue     │  (multiprocessing.Queue)  │
│              └──────────────────────┘                           │
│                         │                                        │
│                         ▼                                        │
│  CONSUMER (Subprocess)                                           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  while True:                                               │  │
│  │      command = command_queue.get()  # Blocking             │  │
│  │      result = process(command)                             │  │
│  │      result_queue.put(result)                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                         │                                        │
│                         ▼                                        │
│              ┌──────────────────────┐                           │
│              │     result_queue     │  (multiprocessing.Queue)  │
│              └──────────────────────┘                           │
│                         │                                        │
│                         ▼                                        │
│  PRODUCER (Main Process)                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  result = engine.get_result()                              │  │
│  │      │                                                     │  │
│  │      ▼                                                     │  │
│  │  result_queue.get(timeout=1.0)  # Non-blocking             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

### 11. Async/Await Pattern

**Purpose**: Non-blocking I/O operations throughout the backend.

**Location**: Throughout backend

```python
# Async route handler
@router.get('/{analysis_id}')
async def get_analysis(
    analysis_id: str,
    session: AsyncSession = Depends(get_db)
) -> AnalysisResponseSchema:
    return await service.get_analysis(session, analysis_id)

# Async service
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

# Async database session
async with AsyncSessionLocal() as session:
    await session.execute(query)
    await session.commit()
```

**Benefits**:
- Non-blocking I/O
- High concurrency for I/O-bound operations
- Efficient resource utilization

---

## Data Patterns

### 12. Lazy Evaluation Pattern

**Purpose**: Defer computation until results are needed.

**Location**: `backend/modules/compute/engine.py`

```python
def _execute_pipeline(datasource_config: dict, steps: list[dict]) -> dict:
    # 1. Create LazyFrame (no data loaded yet)
    if datasource_config['source_type'] == 'file':
        file_path = datasource_config['config']['file_path']
        file_type = datasource_config['config']['file_type']

        if file_type == 'csv':
            lf = pl.scan_csv(file_path)      # Lazy - no I/O
        elif file_type == 'parquet':
            lf = pl.scan_parquet(file_path)  # Lazy - no I/O

    # 2. Build transformation pipeline (all lazy)
    for step in ordered_steps:
        operation = step['operation']
        params = step['params']

        if operation == 'filter':
            lf = lf.filter(build_filter_expr(params))  # Lazy
        elif operation == 'select':
            lf = lf.select(params['columns'])          # Lazy
        elif operation == 'group_by':
            lf = lf.group_by(params['group_by']).agg(  # Lazy
                build_agg_exprs(params['aggregations'])
            )

    # 3. Single point of materialization
    df = lf.collect()  # Actually executes everything

    return {
        'schema': dict(df.schema),
        'row_count': len(df),
        'sample_data': df.head(5000).to_dicts()
    }
```

**Benefits**:
- Query optimization by Polars
- Memory efficiency
- Single execution pass

---

### 13. Caching Pattern

**Purpose**: Cache expensive computations to avoid redundant work.

**Frontend Schema Cache**:
```typescript
// stores/datasource.svelte.ts
class DatasourceStore {
  schemas = $state(new Map<string, SchemaInfo>());

  async getSchema(id: string): Promise<SchemaInfo> {
    // Check cache first
    const cached = this.schemas.get(id);
    if (cached) return cached;

    // Fetch and cache
    const schema = await getDatasourceSchema(id);
    this.schemas.set(id, schema);
    return schema;
  }
}

// Schema calculator cache
class SchemaCalculator {
  private cache = $state(new SvelteMap<string, Schema>());

  calculateSchema(baseSchema: Schema, steps: PipelineStep[]): Schema {
    for (const step of orderedSteps) {
      const cached = this.cache.get(step.id);
      if (cached) {
        schema = cached;
        continue;
      }

      schema = applyTransformation(schema, step);
      this.cache.set(step.id, schema);
    }
    return schema;
  }
}
```

**Backend Schema Cache**:
```python
# datasource/models.py
class DataSource(Base):
    schema_cache: Mapped[dict | None] = mapped_column(JSON, nullable=True)

# datasource/service.py
async def get_schema(session: AsyncSession, datasource_id: str) -> SchemaInfo:
    datasource = await get_datasource(session, datasource_id)

    # Return cached if available
    if datasource.schema_cache:
        return SchemaInfo.model_validate(datasource.schema_cache)

    # Extract and cache
    schema = await _extract_schema(datasource)
    datasource.schema_cache = schema.model_dump()
    await session.commit()
    return schema
```

---

## Frontend Patterns

### 14. Component Composition Pattern

**Purpose**: Build complex UIs from smaller, reusable components.

**Location**: `frontend/src/lib/components/`

```svelte
<!-- PipelineCanvas.svelte (Composite) -->
<script lang="ts">
  import DatasourceNode from './DatasourceNode.svelte';
  import StepNode from './StepNode.svelte';
  import ConnectionLine from './ConnectionLine.svelte';
</script>

<div class="canvas">
  <!-- Data source nodes -->
  {#each datasources as ds}
    <DatasourceNode datasource={ds} />
  {/each}

  <!-- Connection lines -->
  {#each connections as conn}
    <ConnectionLine
      from={conn.from}
      to={conn.to}
    />
  {/each}

  <!-- Step nodes -->
  {#each steps as step}
    <StepNode
      {step}
      onSelect={() => selectStep(step.id)}
      onDelete={() => deleteStep(step.id)}
    />
  {/each}
</div>

<!-- StepNode.svelte (Leaf) -->
<script lang="ts">
  let { step, onSelect, onDelete } = $props();
</script>

<div
  class="step-node"
  onclick={onSelect}
  draggable="true"
>
  <span class="type">{step.type}</span>
  <button onclick={onDelete}>Delete</button>
</div>
```

---

### 15. Store Pattern (Svelte Runes)

**Purpose**: Centralized, reactive state management.

**Location**: `frontend/src/lib/stores/`

```typescript
// Class-based store with Svelte 5 runes
class AnalysisStore {
  // Mutable state
  current = $state<Analysis | null>(null);
  tabs = $state<AnalysisTab[]>([]);
  activeTabId = $state<string | null>(null);
  loading = $state(false);
  error = $state<string | null>(null);

  // Derived state (computed)
  activeTab = $derived(
    this.tabs.find(t => t.id === this.activeTabId) ?? null
  );

  pipeline = $derived(this.activeTab?.steps ?? []);

  // Actions
  async loadAnalysis(id: string): Promise<void> {
    this.loading = true;
    this.error = null;
    try {
      this.current = await getAnalysis(id);
      this.tabs = this.current.tabs;
      this.activeTabId = this.tabs[0]?.id ?? null;
    } catch (err) {
      this.error = err instanceof Error ? err.message : 'Failed to load';
    } finally {
      this.loading = false;
    }
  }

  addStep(step: PipelineStep): void {
    if (!this.activeTab) return;
    this.activeTab.steps = [...this.activeTab.steps, step];
  }

  updateStep(stepId: string, config: OperationConfig): void {
    if (!this.activeTab) return;
    this.activeTab.steps = this.activeTab.steps.map(s =>
      s.id === stepId ? { ...s, config } : s
    );
  }
}

// Export singleton instance
export const analysisStore = new AnalysisStore();
```

---

### 16. Props Down, Events Up Pattern

**Purpose**: Unidirectional data flow in component hierarchy.

```svelte
<!-- Parent: StepConfig.svelte -->
<script lang="ts">
  import FilterConfig from '../operations/FilterConfig.svelte';
  import { analysisStore } from '$lib/stores';

  let { step } = $props();

  function handleConfigChange(newConfig: OperationConfig) {
    analysisStore.updateStep(step.id, newConfig);
  }
</script>

<!-- Props down -->
{#if step.type === 'filter'}
  <FilterConfig
    config={step.config}
    schema={schema}
    onchange={handleConfigChange}  <!-- Events up -->
  />
{/if}

<!-- Child: FilterConfig.svelte -->
<script lang="ts">
  let { config, schema, onchange } = $props();

  function updateCondition(index: number, field: string, value: any) {
    const newConditions = [...config.conditions];
    newConditions[index] = { ...newConditions[index], [field]: value };

    // Event up to parent
    onchange({ ...config, conditions: newConditions });
  }
</script>

<select onchange={(e) => updateCondition(0, 'column', e.target.value)}>
  {#each schema.columns as col}
    <option value={col.name}>{col.name}</option>
  {/each}
</select>
```

---

## Summary

| Category | Pattern | Location |
|----------|---------|----------|
| **Architectural** | Monorepo | Project root |
| **Architectural** | Layered | Backend modules |
| **Architectural** | Modular | Backend modules |
| **Structural** | Singleton | ProcessManager |
| **Structural** | Repository | Service layer |
| **Structural** | Dependency Injection | FastAPI Depends |
| **Behavioral** | Strategy | Step converter |
| **Behavioral** | Observer | Svelte stores |
| **Behavioral** | Command | Compute engine |
| **Concurrency** | Producer-Consumer | IPC queues |
| **Concurrency** | Async/Await | Throughout backend |
| **Data** | Lazy Evaluation | Polars pipeline |
| **Data** | Caching | Schema caches |
| **Frontend** | Component Composition | Svelte components |
| **Frontend** | Store | Svelte runes |
| **Frontend** | Props Down/Events Up | Component hierarchy |

---

## See Also

- [System Design](./system-design.md) - Architecture overview
- [Data Flow](./data-flow.md) - Request/response flows
- [Technology Decisions](./technology-decisions.md) - Why these patterns
