# Data Flow

This document provides comprehensive documentation of how data flows through the Polars-FastAPI-Svelte Analysis Platform.

## Table of Contents

1. [Overview](#overview)
2. [Data Source Creation Flow](#data-source-creation-flow)
3. [Analysis Creation Flow](#analysis-creation-flow)
4. [Pipeline Building Flow](#pipeline-building-flow)
5. [Pipeline Execution Flow](#pipeline-execution-flow)
6. [Result Retrieval Flow](#result-retrieval-flow)
7. [Schema Calculation Flow](#schema-calculation-flow)
8. [Error Propagation Flow](#error-propagation-flow)

---

## Overview

Data flows through the system in several key pathways:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW OVERVIEW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  USER INPUT                                                                 │
│      │                                                                      │
│      ▼                                                                      │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│  │  Data Source│────►│  Analysis   │────►│  Pipeline   │                   │
│  │  Creation   │     │  Creation   │     │  Building   │                   │
│  └─────────────┘     └─────────────┘     └──────┬──────┘                   │
│                                                 │                           │
│                                                 ▼                           │
│                                          ┌─────────────┐                   │
│                                          │  Execution  │                   │
│                                          └──────┬──────┘                   │
│                                                 │                           │
│                                                 ▼                           │
│                                          ┌─────────────┐                   │
│                                          │   Results   │                   │
│                                          └─────────────┘                   │
│                                                 │                           │
│                                                 ▼                           │
│                                            USER OUTPUT                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Source Creation Flow

### File Upload Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FILE UPLOAD FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: User selects file                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Frontend: <input type="file" onchange={handleFileSelect} />          │  │
│  │                                                                       │  │
│  │  File object captured: { name, size, type }                           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  STEP 2: FormData construction                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  const formData = new FormData();                                     │  │
│  │  formData.append('file', file);                                       │  │
│  │  formData.append('name', datasourceName);                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  STEP 3: HTTP Request                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  POST /api/v1/datasource/upload                                       │  │
│  │  Content-Type: multipart/form-data                                    │  │
│  │  Body: FormData                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  STEP 4: Backend file handling                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  routes.py:                                                           │  │
│  │  1. Validate file extension (.csv, .parquet, .json, .xlsx)            │  │
│  │  2. Generate UUID filename: {uuid}{extension}                         │  │
│  │  3. Write to ./data/uploads/{uuid}{extension}                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  STEP 5: Database record creation                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  service.py:                                                          │  │
│  │  DataSource(                                                          │  │
│  │      id=uuid4(),                                                      │  │
│  │      name=user_provided_name,                                         │  │
│  │      source_type='file',                                              │  │
│  │      config={                                                         │  │
│  │          'file_path': './data/uploads/{uuid}.csv',                    │  │
│  │          'file_type': 'csv'                                           │  │
│  │      },                                                               │  │
│  │      schema_cache=None,                                               │  │
│  │      created_at=now()                                                 │  │
│  │  )                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  STEP 6: Schema extraction (lazy)                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  service.py._extract_schema():                                        │  │
│  │  lf = pl.scan_csv(file_path)  # Lazy, no data loaded                  │  │
│  │  schema = lf.collect_schema() # Get column names and types            │  │
│  │  row_count = lf.select(pl.len()).collect().item()  # Count rows       │  │
│  │                                                                       │  │
│  │  SchemaInfo(                                                          │  │
│  │      columns=[                                                        │  │
│  │          ColumnSchema(name='id', dtype='Int64', nullable=True),       │  │
│  │          ColumnSchema(name='name', dtype='String', nullable=True),    │  │
│  │          ...                                                          │  │
│  │      ],                                                               │  │
│  │      row_count=10000                                                  │  │
│  │  )                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  STEP 7: Response to frontend                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  HTTP 200 OK                                                          │  │
│  │  {                                                                    │  │
│  │      "id": "ds-uuid-123",                                             │  │
│  │      "name": "Sales Data",                                            │  │
│  │      "source_type": "file",                                           │  │
│  │      "config": {...},                                                 │  │
│  │      "schema_cache": {...},                                           │  │
│  │      "created_at": "2024-01-15T10:30:00Z"                             │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  STEP 8: Frontend state update                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  datasourceStore.datasources = [...datasources, newDatasource];       │  │
│  │  // UI automatically updates via Svelte reactivity                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database Connection Flow

```
User Input: { connection_string, query }
    │
    ▼
POST /api/v1/datasource/connect
    │
    ▼
Validate connection string format
    │
    ▼
Create DataSource record:
    config: {
        connection_string: "postgresql://...",
        query: "SELECT * FROM users"
    }
    │
    ▼
(Schema extracted on demand when requested)
    │
    ▼
Return DataSourceResponse
```

---

## Analysis Creation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ANALYSIS CREATION FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FRONTEND: Create Analysis Wizard                                           │
│                                                                             │
│  Step 1: Details                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  User enters:                                                         │  │
│  │  - name: "Q4 Sales Analysis"                                          │  │
│  │  - description: "Analyze Q4 sales trends"                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  Step 2: Data Source Selection                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  User selects datasources from list:                                  │  │
│  │  - [x] Sales Data (ds-uuid-1)                                         │  │
│  │  - [x] Customer Data (ds-uuid-2)                                      │  │
│  │  - [ ] Product Data (ds-uuid-3)                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  Step 3: Review & Create                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Summary shown:                                                       │  │
│  │  - Name: Q4 Sales Analysis                                            │  │
│  │  - Data Sources: 2 selected                                           │  │
│  │  - Click "Create Analysis"                                            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  FRONTEND: API Request                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  POST /api/v1/analysis                                                │  │
│  │  {                                                                    │  │
│  │      "name": "Q4 Sales Analysis",                                     │  │
│  │      "description": "Analyze Q4 sales trends",                        │  │
│  │      "datasource_ids": ["ds-uuid-1", "ds-uuid-2"],                    │  │
│  │      "pipeline_steps": [],                                            │  │
│  │      "tabs": []                                                       │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  BACKEND: Validation                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  service.py:                                                          │  │
│  │  for ds_id in datasource_ids:                                         │  │
│  │      datasource = await get_datasource(session, ds_id)                │  │
│  │      if not datasource:                                               │  │
│  │          raise ValueError(f"DataSource {ds_id} not found")            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  BACKEND: Record Creation                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  1. Create Analysis record:                                           │  │
│  │     Analysis(                                                         │  │
│  │         id="analysis-uuid-123",                                       │  │
│  │         name="Q4 Sales Analysis",                                     │  │
│  │         pipeline_definition={                                         │  │
│  │             "steps": [],                                              │  │
│  │             "datasource_ids": ["ds-uuid-1", "ds-uuid-2"],             │  │
│  │             "tabs": [auto-generated tabs]                             │  │
│  │         },                                                            │  │
│  │         status="draft"                                                │  │
│  │     )                                                                 │  │
│  │                                                                       │  │
│  │  2. Create junction records:                                          │  │
│  │     AnalysisDataSource(analysis_id, datasource_id) for each           │  │
│  │                                                                       │  │
│  │  3. Auto-generate tabs for each datasource:                           │  │
│  │     Tab(                                                              │  │
│  │         id="tab-uuid",                                                │  │
│  │         name="Sales Data",                                            │  │
│  │         type="datasource",                                            │  │
│  │         datasource_id="ds-uuid-1",                                    │  │
│  │         steps=[]                                                      │  │
│  │     )                                                                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  BACKEND: Response                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  HTTP 200 OK                                                          │  │
│  │  AnalysisResponseSchema                                               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  FRONTEND: Navigation                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  goto(`/analysis/${response.id}`);                                    │  │
│  │  // Redirects to pipeline editor                                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Building Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PIPELINE BUILDING FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  USER ACTION: Drag "Filter" from library to canvas                          │
│                              │                                              │
│                              ▼                                              │
│  DRAG STORE: Track drag state                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  drag.start('filter', 'library');                                     │  │
│  │  // type: 'filter', source: 'library', stepId: null                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  USER ACTION: Drop on canvas                                                │
│                              │                                              │
│                              ▼                                              │
│  ANALYSIS STORE: Add step                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  analysisStore.addStep({                                              │  │
│  │      id: crypto.randomUUID(),                                         │  │
│  │      type: 'filter',                                                  │  │
│  │      config: {                                                        │  │
│  │          conditions: [],                                              │  │
│  │          logic: 'AND'                                                 │  │
│  │      },                                                               │  │
│  │      depends_on: [previousStepId]                                     │  │
│  │  });                                                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  SCHEMA CALCULATOR: Update predicted schema (CLIENT-SIDE, NO API)           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  schemaCalculator.calculatePipelineSchema(                            │  │
│  │      baseSchema,  // From datasource                                  │  │
│  │      pipeline     // Updated steps array                              │  │
│  │  );                                                                   │  │
│  │                                                                       │  │
│  │  For 'filter' operation:                                              │  │
│  │  - Schema unchanged (same columns)                                    │  │
│  │  - Row count unknown (depends on data)                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  UI UPDATE: Canvas re-renders with new step                                 │
│                              │                                              │
│                              ▼                                              │
│  USER ACTION: Configure filter (add condition)                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  In FilterConfig component:                                           │  │
│  │  - Select column: "age"                                               │  │
│  │  - Select operator: ">"                                               │  │
│  │  - Enter value: 18                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  ANALYSIS STORE: Update step config                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  analysisStore.updateStep(stepId, {                                   │  │
│  │      conditions: [                                                    │  │
│  │          { column: 'age', operator: '>', value: 18 }                  │  │
│  │      ],                                                               │  │
│  │      logic: 'AND'                                                     │  │
│  │  });                                                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  AUTO-SAVE: Debounced (3 seconds)                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  $effect(() => {                                                      │  │
│  │      // Track pipeline changes                                        │  │
│  │      const pipeline = analysisStore.pipeline;                         │  │
│  │                                                                       │  │
│  │      if (saveTimeout) clearTimeout(saveTimeout);                      │  │
│  │      saveStatus = 'unsaved';                                          │  │
│  │                                                                       │  │
│  │      saveTimeout = setTimeout(async () => {                           │  │
│  │          saveStatus = 'saving';                                       │  │
│  │          await analysisStore.save();                                  │  │
│  │          saveStatus = 'saved';                                        │  │
│  │      }, 3000);                                                        │  │
│  │  });                                                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  API REQUEST: Save to backend                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  PUT /api/v1/analysis/{id}                                            │  │
│  │  {                                                                    │  │
│  │      "pipeline_steps": [...],                                         │  │
│  │      "tabs": [...]                                                    │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PIPELINE EXECUTION FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  USER ACTION: Click "Run Analysis"                                          │
│                              │                                              │
│                              ▼                                              │
│  FRONTEND: Start execution                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  const job = await computeStore.executeAnalysis(analysisId);          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  API REQUEST                                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  POST /api/v1/compute/execute                                         │  │
│  │  { "analysis_id": "analysis-uuid-123" }                               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  BACKEND: Route handler                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  @router.post('/execute')                                             │  │
│  │  async def execute_analysis(data, session, manager):                  │  │
│  │      # 1. Get analysis from DB                                        │  │
│  │      analysis = await get_analysis(session, data.analysis_id)         │  │
│  │                                                                       │  │
│  │      # 2. Get datasource config                                       │  │
│  │      datasource_id = analysis.pipeline_definition['datasource_ids'][0]│  │
│  │      datasource = await get_datasource(session, datasource_id)        │  │
│  │                                                                       │  │
│  │      # 3. Get or create compute engine                                │  │
│  │      engine_info = manager.get_or_create_engine(data.analysis_id)     │  │
│  │                                                                       │  │
│  │      # 4. Queue execution                                             │  │
│  │      job = await execute_analysis(                                    │  │
│  │          session, datasource_id, analysis.pipeline_definition['steps']│  │
│  │      )                                                                │  │
│  │      return ComputeStatusSchema(job_id=job.id, status='pending')      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  PROCESS MANAGER: Engine management                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  def get_or_create_engine(analysis_id):                               │  │
│  │      if analysis_id in self._engines:                                 │  │
│  │          return self._engines[analysis_id]  # Reuse existing          │  │
│  │                                                                       │  │
│  │      # Create new engine                                              │  │
│  │      engine = PolarsComputeEngine(analysis_id)                        │  │
│  │      engine.start()  # Starts subprocess                              │  │
│  │      self._engines[analysis_id] = EngineInfo(engine)                  │  │
│  │      return self._engines[analysis_id]                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  COMPUTE ENGINE: Queue command                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  engine.execute(job_id, datasource_config, pipeline_steps)            │  │
│  │                                                                       │  │
│  │  command_queue.put({                                                  │  │
│  │      'type': 'execute',                                               │  │
│  │      'job_id': 'job-uuid-456',                                        │  │
│  │      'datasource_config': {                                           │  │
│  │          'source_type': 'file',                                       │  │
│  │          'config': {'file_path': '...', 'file_type': 'csv'}           │  │
│  │      },                                                               │  │
│  │      'pipeline_steps': [                                              │  │
│  │          {'id': 'step-1', 'type': 'filter', 'config': {...}},         │  │
│  │          {'id': 'step-2', 'type': 'select', 'config': {...}}          │  │
│  │      ]                                                                │  │
│  │  })                                                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│        ┌─────────────────────┴─────────────────────┐                       │
│        │                                           │                       │
│        ▼                                           ▼                       │
│  MAIN PROCESS: Return response         SUBPROCESS: Execute pipeline         │
│  ┌───────────────────────────┐         ┌───────────────────────────────┐   │
│  │  Return to frontend:      │         │  while True:                  │   │
│  │  {                        │         │      cmd = command_queue.get()│   │
│  │      job_id: "job-uuid",  │         │      if cmd.type == 'execute':│   │
│  │      status: "pending"    │         │          result = process(cmd)│   │
│  │  }                        │         │          result_queue.put(..) │   │
│  └───────────────────────────┘         └───────────────────────────────┘   │
│                              │                         │                   │
│                              ▼                         │                   │
│  FRONTEND: Start polling                               │                   │
│  ┌───────────────────────────────────────────────────┐ │                   │
│  │  computeStore.startPolling(jobId);                │ │                   │
│  │                                                   │ │                   │
│  │  setInterval(async () => {                        │ │                   │
│  │      const status = await getComputeStatus(jobId);│ │                   │
│  │      updateJobState(status);                      │ │                   │
│  │      if (isTerminal(status)) stopPolling();       │ │                   │
│  │  }, 2000);  // Every 2 seconds                    │ │                   │
│  └───────────────────────────────────────────────────┘ │                   │
│                              │                         │                   │
│                              │                         ▼                   │
│                              │         SUBPROCESS: Pipeline execution       │
│                              │         ┌───────────────────────────────┐   │
│                              │         │  1. Load datasource:          │   │
│                              │         │     lf = pl.scan_csv(path)    │   │
│                              │         │                               │   │
│                              │         │  2. Convert steps:            │   │
│                              │         │     backend_steps = convert() │   │
│                              │         │                               │   │
│                              │         │  3. Topological sort:         │   │
│                              │         │     ordered = topo_sort(steps)│   │
│                              │         │                               │   │
│                              │         │  4. Apply each step:          │   │
│                              │         │     for step in ordered:      │   │
│                              │         │         lf = apply(lf, step)  │   │
│                              │         │                               │   │
│                              │         │  5. Collect result:           │   │
│                              │         │     df = lf.collect()         │   │
│                              │         │                               │   │
│                              │         │  6. Format output:            │   │
│                              │         │     {                         │   │
│                              │         │         schema: {...},        │   │
│                              │         │         row_count: 5000,      │   │
│                              │         │         sample_data: [...]    │   │
│                              │         │     }                         │   │
│                              │         └───────────────────────────────┘   │
│                              │                         │                   │
│                              │                         ▼                   │
│                              │         result_queue.put({                  │
│                              │             job_id: "job-uuid",             │
│                              │             status: "completed",            │
│                              │             data: {...}                     │
│                              │         })                                  │
│                              │                         │                   │
│                              ◄─────────────────────────┘                   │
│                              │                                              │
│                              ▼                                              │
│  POLLING: Get completed status                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  GET /api/v1/compute/status/{job_id}                                  │  │
│  │                                                                       │  │
│  │  Backend checks result_queue:                                         │  │
│  │  result = engine.get_result()  # Non-blocking                         │  │
│  │                                                                       │  │
│  │  Returns:                                                             │  │
│  │  {                                                                    │  │
│  │      "job_id": "job-uuid",                                            │  │
│  │      "status": "completed",                                           │  │
│  │      "progress": 1.0,                                                 │  │
│  │      "data": {...}                                                    │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  FRONTEND: Stop polling, display results                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  computeStore.stopPolling(jobId);                                     │  │
│  │  // UI updates to show results                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Result Retrieval Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       RESULT RETRIEVAL FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STORAGE: Result stored as Parquet                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  ./data/results/{analysis_id}.parquet                                 │  │
│  │                                                                       │  │
│  │  After execution completes:                                           │  │
│  │  df.write_parquet(f'./data/results/{analysis_id}.parquet')            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  REQUEST: Get result metadata                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  GET /api/v1/results/{analysis_id}                                    │  │
│  │                                                                       │  │
│  │  Backend:                                                             │  │
│  │  df = pl.scan_parquet(result_path)                                    │  │
│  │  schema = df.collect_schema()                                         │  │
│  │  row_count = df.select(pl.len()).collect().item()                     │  │
│  │                                                                       │  │
│  │  Response:                                                            │  │
│  │  {                                                                    │  │
│  │      "analysis_id": "...",                                            │  │
│  │      "row_count": 10000,                                              │  │
│  │      "column_count": 5,                                               │  │
│  │      "columns_schema": [...],                                         │  │
│  │      "created_at": "..."                                              │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  REQUEST: Get paginated data                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  GET /api/v1/results/{analysis_id}/data?page=1&page_size=100          │  │
│  │                                                                       │  │
│  │  Backend:                                                             │  │
│  │  df = pl.scan_parquet(result_path)                                    │  │
│  │  offset = (page - 1) * page_size  # 0                                 │  │
│  │  data = df.slice(offset, page_size).collect()                         │  │
│  │                                                                       │  │
│  │  Response:                                                            │  │
│  │  {                                                                    │  │
│  │      "columns": ["id", "name", "age", ...],                           │  │
│  │      "data": [                                                        │  │
│  │          {"id": 1, "name": "Alice", "age": 30},                       │  │
│  │          {"id": 2, "name": "Bob", "age": 25},                         │  │
│  │          ...                                                          │  │
│  │      ],                                                               │  │
│  │      "total_count": 10000,                                            │  │
│  │      "page": 1,                                                       │  │
│  │      "page_size": 100                                                 │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  REQUEST: Export result                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  POST /api/v1/results/{analysis_id}/export                            │  │
│  │  { "format": "csv" }                                                  │  │
│  │                                                                       │  │
│  │  Backend:                                                             │  │
│  │  df = pl.read_parquet(result_path)                                    │  │
│  │  export_path = f'{results_dir}/{analysis_id}.csv'                     │  │
│  │  df.write_csv(export_path)                                            │  │
│  │                                                                       │  │
│  │  Response:                                                            │  │
│  │  FileResponse(path=export_path, filename=f'{analysis_id}.csv')        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Schema Calculation Flow

The schema calculator predicts output schema **client-side** without making API calls:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLIENT-SIDE SCHEMA CALCULATION                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT: Base schema (from datasource) + Pipeline steps                      │
│                                                                             │
│  Base Schema:                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  columns: [                                                           │  │
│  │      { name: 'id', dtype: 'Int64' },                                  │  │
│  │      { name: 'name', dtype: 'String' },                               │  │
│  │      { name: 'age', dtype: 'Int64' },                                 │  │
│  │      { name: 'city', dtype: 'String' },                               │  │
│  │      { name: 'salary', dtype: 'Float64' }                             │  │
│  │  ],                                                                   │  │
│  │  row_count: 10000                                                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  STEP 1: Filter (age > 18)                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Transformation rule: Schema unchanged, row_count unknown             │  │
│  │                                                                       │  │
│  │  Output:                                                              │  │
│  │  columns: [same as input]                                             │  │
│  │  row_count: null  // Can't predict without data                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  STEP 2: Select (name, age, salary)                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Transformation rule: Keep only selected columns                      │  │
│  │                                                                       │  │
│  │  Output:                                                              │  │
│  │  columns: [                                                           │  │
│  │      { name: 'name', dtype: 'String' },                               │  │
│  │      { name: 'age', dtype: 'Int64' },                                 │  │
│  │      { name: 'salary', dtype: 'Float64' }                             │  │
│  │  ],                                                                   │  │
│  │  row_count: null                                                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  STEP 3: GroupBy (group by age, sum salary)                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Transformation rule:                                                 │  │
│  │  - Keep group_by columns                                              │  │
│  │  - Add aggregation columns with inferred types                        │  │
│  │                                                                       │  │
│  │  Output:                                                              │  │
│  │  columns: [                                                           │  │
│  │      { name: 'age', dtype: 'Int64' },         // Group key            │  │
│  │      { name: 'total_salary', dtype: 'Float64' } // sum(Float64)       │  │
│  │  ],                                                                   │  │
│  │  row_count: null                                                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  OUTPUT: Predicted schema displayed in UI                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  <SchemaViewer schema={calculatedSchema} />                           │  │
│  │                                                                       │  │
│  │  | Column       | Type    |                                           │  │
│  │  |--------------|---------|                                           │  │
│  │  | age          | Int64   |                                           │  │
│  │  | total_salary | Float64 |                                           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Error Propagation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ERROR PROPAGATION FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ERROR SOURCE: Compute subprocess                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  try:                                                                 │  │
│  │      result = execute_pipeline(...)                                   │  │
│  │  except Exception as e:                                               │  │
│  │      result_queue.put({                                               │  │
│  │          'job_id': job_id,                                            │  │
│  │          'status': 'failed',                                          │  │
│  │          'error': str(e)                                              │  │
│  │      })                                                               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  BACKEND: Service layer receives error                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  result = engine.get_result()                                         │  │
│  │  if result and result.get('status') == 'failed':                      │  │
│  │      _job_status[job_id] = {                                          │  │
│  │          'status': JobStatus.FAILED,                                  │  │
│  │          'error_message': result.get('error')                         │  │
│  │      }                                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  API: Return error status                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  GET /api/v1/compute/status/{job_id}                                  │  │
│  │                                                                       │  │
│  │  Response:                                                            │  │
│  │  {                                                                    │  │
│  │      "job_id": "...",                                                 │  │
│  │      "status": "failed",                                              │  │
│  │      "error_message": "Column 'invalid' not found"                    │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  FRONTEND: Handle error in store                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  async pollJobStatus(jobId) {                                         │  │
│  │      const job = await getComputeStatus(jobId);                       │  │
│  │      this.jobs.set(jobId, job);                                       │  │
│  │                                                                       │  │
│  │      if (job.status === 'failed') {                                   │  │
│  │          this.stopPolling(jobId);                                     │  │
│  │          // Error available via job.error                             │  │
│  │      }                                                                │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  UI: Display error to user                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  {#if job.status === 'failed'}                                        │  │
│  │      <div class="error">                                              │  │
│  │          Execution failed: {job.error}                                │  │
│  │      </div>                                                           │  │
│  │  {/if}                                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ERROR SOURCE: API validation                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Service layer:                                                       │  │
│  │  if not datasource:                                                   │  │
│  │      raise ValueError(f'DataSource {id} not found')                   │  │
│  │                                                                       │  │
│  │  Route handler:                                                       │  │
│  │  except ValueError as e:                                              │  │
│  │      raise HTTPException(status_code=400, detail=str(e))              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  API Response: HTTP 400                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  {                                                                    │  │
│  │      "detail": "DataSource ds-invalid not found"                      │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  FRONTEND: API client throws                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  if (!response.ok) {                                                  │  │
│  │      throw new ApiError(                                              │  │
│  │          errorText,                                                   │  │
│  │          response.status,                                             │  │
│  │          response.statusText                                          │  │
│  │      );                                                               │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  FRONTEND: Store catches and updates state                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  try {                                                                │  │
│  │      await apiCall();                                                 │  │
│  │  } catch (err) {                                                      │  │
│  │      this.error = err instanceof Error ? err.message : 'Failed';      │  │
│  │  }                                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│  UI: Display error                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  {#if store.error}                                                    │  │
│  │      <div class="error">{store.error}</div>                           │  │
│  │  {/if}                                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## See Also

- [System Design](./system-design.md) - Architecture overview
- [Design Patterns](./design-patterns.md) - Pattern implementations
- [Technology Decisions](./technology-decisions.md) - Why these choices
