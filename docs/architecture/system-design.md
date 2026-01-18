# System Design

This document provides a comprehensive overview of the system design for the Polars-FastAPI-Svelte Analysis Platform.

## Table of Contents

1. [Overview](#overview)
2. [System Components](#system-components)
3. [Frontend Architecture](#frontend-architecture)
4. [Backend Architecture](#backend-architecture)
5. [Compute Architecture](#compute-architecture)
6. [Storage Architecture](#storage-architecture)
7. [Communication Patterns](#communication-patterns)
8. [Scalability Considerations](#scalability-considerations)

---

## Overview

The platform is designed as a **three-tier architecture** with clear separation between presentation (frontend), application (backend), and data (storage/compute) layers. The system operates entirely locally, with no external dependencies.

### Design Goals

| Goal | Implementation |
|------|----------------|
| **Performance** | Polars lazy evaluation, multiprocessing isolation |
| **Usability** | Visual pipeline builder, real-time feedback |
| **Extensibility** | Modular architecture, clear interfaces |
| **Reliability** | Type safety, comprehensive error handling |
| **Simplicity** | SQLite storage, no external services |

---

## System Components

### Component Inventory

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SYSTEM COMPONENTS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FRONTEND (SvelteKit)                                                       │
│  ├── Routes (5 pages)                                                       │
│  │   ├── / (Gallery)                                                        │
│  │   ├── /analysis/new (Create Wizard)                                      │
│  │   ├── /analysis/[id] (Pipeline Editor)                                   │
│  │   ├── /datasources (Data Source List)                                    │
│  │   └── /datasources/new (Create Data Source)                              │
│  ├── Components (36 components)                                             │
│  │   ├── Pipeline (6): Canvas, Node, Library, Config, Line, Datasource      │
│  │   ├── Operations (20+): Filter, Select, GroupBy, Join, etc.              │
│  │   ├── Viewers (4): DataTable, InlineTable, Schema, Stats                 │
│  │   └── Gallery (4): Card, Filters, Grid, Empty                            │
│  ├── Stores (4 reactive stores)                                             │
│  │   ├── analysisStore                                                      │
│  │   ├── datasourceStore                                                    │
│  │   ├── computeStore                                                       │
│  │   └── drag                                                               │
│  ├── API Client (5 modules)                                                 │
│  │   ├── client.ts (base)                                                   │
│  │   ├── analysis.ts                                                        │
│  │   ├── datasource.ts                                                      │
│  │   ├── compute.ts                                                         │
│  │   └── health.ts                                                          │
│  └── Schema Calculator (client-side prediction)                             │
│                                                                             │
│  BACKEND (FastAPI)                                                          │
│  ├── Core (2 modules)                                                       │
│  │   ├── config.py (Pydantic settings)                                      │
│  │   └── database.py (SQLAlchemy setup)                                     │
│  ├── Modules (5 feature modules)                                            │
│  │   ├── analysis/ (CRUD, pipeline management)                              │
│  │   ├── datasource/ (file upload, connections)                             │
│  │   ├── compute/ (execution, preview, engine lifecycle)                    │
│  │   ├── results/ (retrieval, pagination, export)                           │
│  │   └── health/ (status check)                                             │
│  └── API Router (versioned: /api/v1)                                        │
│                                                                             │
│  COMPUTE ENGINE                                                             │
│  ├── ProcessManager (singleton, engine pool)                                │
│  ├── PolarsComputeEngine (subprocess, queue IPC)                            │
│  └── StepConverter (frontend → backend format)                              │
│                                                                             │
│  STORAGE                                                                    │
│  ├── SQLite Database (./database/app.db)                                    │
│  │   ├── analyses table                                                     │
│  │   ├── datasources table                                                  │
│  │   └── analysis_datasources junction                                      │
│  └── File System                                                            │
│      ├── ./data/uploads/ (raw data files)                                   │
│      └── ./data/results/ (computed parquet)                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Frontend Architecture

### SvelteKit Application Structure

```
frontend/src/
├── routes/                          # File-based routing
│   ├── +layout.svelte              # Root layout (header, nav)
│   ├── +layout.ts                  # Layout data loading
│   ├── +page.svelte                # Gallery page (/)
│   ├── analysis/
│   │   ├── new/+page.svelte        # Create wizard
│   │   └── [id]/
│   │       ├── +page.svelte        # Pipeline editor
│   │       └── +page.ts            # Analysis data loading
│   └── datasources/
│       └── +page.svelte            # Data source list
│
└── lib/                             # Shared code
    ├── api/                         # HTTP client layer
    ├── components/                  # Svelte components
    ├── stores/                      # Reactive state
    ├── types/                       # TypeScript definitions
    └── utils/                       # Utilities (schema calc)
```

### Component Hierarchy

```
+layout.svelte (Root)
├── Header
│   ├── Navigation
│   └── ThemeToggle
│
├── +page.svelte (Gallery)
│   ├── AnalysisFilters
│   ├── GalleryGrid
│   │   └── AnalysisCard (repeated)
│   └── EmptyState (conditional)
│
├── analysis/new/+page.svelte (Wizard)
│   ├── Step 1: Details Form
│   ├── Step 2: DataSource Selection
│   └── Step 3: Review & Create
│
├── analysis/[id]/+page.svelte (Editor)
│   ├── LeftPane
│   │   └── StepLibrary
│   ├── CenterPane
│   │   └── PipelineCanvas
│   │       ├── DatasourceNode (repeated)
│   │       ├── StepNode (repeated)
│   │       └── ConnectionLine (repeated)
│   └── RightPane
│       └── StepConfig
│           └── [OperationConfig] (dynamic)
│               ├── FilterConfig
│               ├── SelectConfig
│               ├── GroupByConfig
│               └── ... (20+ configs)
│
└── datasources/+page.svelte
    └── DataSourceTable
```

### State Management Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STATE ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      REACTIVE STATE (Svelte Runes)                   │   │
│  │                                                                      │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │   │
│  │  │ analysisStore  │  │datasourceStore │  │  computeStore  │        │   │
│  │  ├────────────────┤  ├────────────────┤  ├────────────────┤        │   │
│  │  │ current        │  │ datasources[]  │  │ jobs Map       │        │   │
│  │  │ tabs[]         │  │ schemas Map    │  │ polling Map    │        │   │
│  │  │ activeTabId    │  │ loading        │  └────────────────┘        │   │
│  │  │ sourceSchemas  │  │ error          │                            │   │
│  │  │ loading/error  │  └────────────────┘  ┌────────────────┐        │   │
│  │  └────────────────┘                      │     drag       │        │   │
│  │                                          ├────────────────┤        │   │
│  │  DERIVED STATE                           │ type           │        │   │
│  │  ├── activeTab (from tabs + activeTabId) │ stepId         │        │   │
│  │  ├── pipeline (from activeTab.steps)     │ source         │        │   │
│  │  └── calculatedSchema (from pipeline)    │ target/valid   │        │   │
│  │                                          └────────────────┘        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      SERVER STATE (TanStack Query)                   │   │
│  │                                                                      │   │
│  │  Query Cache (5-minute stale time)                                  │   │
│  │  ├── ['analyses'] → Analysis[]                                      │   │
│  │  ├── ['analysis', id] → Analysis                                    │   │
│  │  ├── ['datasources'] → DataSource[]                                 │   │
│  │  └── ['datasource', id, 'schema'] → SchemaInfo                      │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

### Application Structure

```
backend/
├── main.py                          # FastAPI application entry
│   ├── Lifespan management          # Startup/shutdown hooks
│   ├── CORS middleware              # Cross-origin configuration
│   └── Router registration          # API routes mounting
│
├── core/
│   ├── config.py                    # Settings (Pydantic)
│   │   ├── App settings             # name, version, debug
│   │   ├── CORS settings            # origins list
│   │   ├── Database settings        # connection URL
│   │   ├── Storage settings         # paths, limits
│   │   └── Compute settings         # timeouts, TTL
│   │
│   └── database.py                  # SQLAlchemy setup
│       ├── Engine creation          # Async SQLite
│       ├── Session factory          # AsyncSessionLocal
│       ├── Base model               # DeclarativeBase
│       └── Dependency               # get_db()
│
├── api/
│   ├── router.py                    # /api prefix
│   └── v1/router.py                 # /api/v1 includes modules
│
└── modules/
    ├── analysis/                    # Analysis management
    ├── datasource/                  # Data source management
    ├── compute/                     # Computation execution
    ├── results/                     # Result handling
    └── health/                      # Health checks
```

### Module Internal Structure

Each module follows a layered pattern:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MODULE STRUCTURE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         routes.py (HTTP Layer)                       │   │
│  │                                                                      │   │
│  │  @router.post('/')                                                   │   │
│  │  async def create_resource(                                          │   │
│  │      data: CreateSchema,                    ◄── Request validation   │   │
│  │      session: AsyncSession = Depends(get_db)◄── Dependency injection │   │
│  │  ) -> ResponseSchema:                       ◄── Response model       │   │
│  │      return await service.create(session, data)                      │   │
│  │                                                                      │   │
│  └──────────────────────────────────┬──────────────────────────────────┘   │
│                                     │                                       │
│                                     ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        service.py (Business Layer)                   │   │
│  │                                                                      │   │
│  │  async def create(session: AsyncSession, data: CreateSchema):        │   │
│  │      # Validate business rules                                       │   │
│  │      # Transform data                                                │   │
│  │      # Call ORM operations                                           │   │
│  │      # Return response                                               │   │
│  │                                                                      │   │
│  └──────────────────────────────────┬──────────────────────────────────┘   │
│                                     │                                       │
│                                     ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        models.py (Data Layer)                        │   │
│  │                                                                      │   │
│  │  class Resource(Base):                                               │   │
│  │      __tablename__ = 'resources'                                     │   │
│  │      id: Mapped[str] = mapped_column(String, primary_key=True)       │   │
│  │      name: Mapped[str] = mapped_column(String, nullable=False)       │   │
│  │      config: Mapped[dict] = mapped_column(JSON)                      │   │
│  │                                                                      │   │
│  └──────────────────────────────────┬──────────────────────────────────┘   │
│                                     │                                       │
│                                     ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       schemas.py (Contract Layer)                    │   │
│  │                                                                      │   │
│  │  class CreateSchema(BaseModel):                                      │   │
│  │      name: str                                                       │   │
│  │      config: dict                                                    │   │
│  │                                                                      │   │
│  │  class ResponseSchema(BaseModel):                                    │   │
│  │      id: str                                                         │   │
│  │      name: str                                                       │   │
│  │      created_at: datetime                                            │   │
│  │      model_config = ConfigDict(from_attributes=True)                 │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Request Processing Flow

```
HTTP Request
     │
     ▼
┌─────────────────┐
│   Middleware    │  CORS, Logging
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Router        │  Path matching, method dispatch
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dependency    │  Session injection, auth (future)
│   Injection     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Pydantic      │  Request body validation
│   Validation    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Route         │  Controller logic
│   Handler       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Service       │  Business logic
│   Layer         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ORM /         │  Database or compute
│   Compute       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Response      │  Pydantic serialization
│   Model         │
└─────────────────┘
         │
         ▼
HTTP Response
```

---

## Compute Architecture

### Multiprocessing Design

The compute engine uses **multiprocessing** to isolate CPU-intensive Polars operations from the main FastAPI process:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMPUTE ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MAIN PROCESS (FastAPI)                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │                  ProcessManager (Singleton)                     │ │   │
│  │  │                                                                 │ │   │
│  │  │  _engines: dict[str, EngineInfo]                               │ │   │
│  │  │                                                                 │ │   │
│  │  │  Methods:                                                       │ │   │
│  │  │  ├── spawn_engine(analysis_id) → EngineInfo                    │ │   │
│  │  │  ├── get_or_create_engine(analysis_id) → EngineInfo            │ │   │
│  │  │  ├── keepalive(analysis_id)                                    │ │   │
│  │  │  ├── get_engine_status(analysis_id) → EngineStatus             │ │   │
│  │  │  ├── shutdown_engine(analysis_id)                              │ │   │
│  │  │  ├── cleanup_idle_engines() → list[str]                        │ │   │
│  │  │  └── shutdown_all()                                            │ │   │
│  │  │                                                                 │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  │                              │                                       │   │
│  │                              │ manages                               │   │
│  │                              ▼                                       │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │                     EngineInfo                                  │ │   │
│  │  │                                                                 │ │   │
│  │  │  engine: PolarsComputeEngine                                   │ │   │
│  │  │  last_activity: datetime                                       │ │   │
│  │  │  status: EngineStatus (idle, running, error, terminated)       │ │   │
│  │  │                                                                 │ │   │
│  │  │  is_idle_for(seconds: int) → bool                              │ │   │
│  │  │  touch() → updates last_activity                               │ │   │
│  │  │                                                                 │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                     │                                       │
│                          command_queue (multiprocessing.Queue)              │
│                          result_queue (multiprocessing.Queue)               │
│                                     │                                       │
│                                     ▼                                       │
│  SUBPROCESS (PolarsComputeEngine)                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Event Loop:                                                         │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │  while True:                                                    │ │   │
│  │  │      command = command_queue.get()                              │ │   │
│  │  │      if command['type'] == 'shutdown':                          │ │   │
│  │  │          break                                                  │ │   │
│  │  │      if command['type'] == 'execute':                           │ │   │
│  │  │          try:                                                   │ │   │
│  │  │              result = _execute_pipeline(command)                │ │   │
│  │  │              result_queue.put({status: COMPLETED, data: ...})   │ │   │
│  │  │          except Exception as e:                                 │ │   │
│  │  │              result_queue.put({status: FAILED, error: str(e)})  │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                      │   │
│  │  Pipeline Execution:                                                 │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │  1. Load datasource → Polars LazyFrame                         │ │   │
│  │  │  2. Convert steps (frontend → backend format)                   │ │   │
│  │  │  3. Build dependency graph                                      │ │   │
│  │  │  4. Topological sort (detect cycles)                            │ │   │
│  │  │  5. Apply operations sequentially                               │ │   │
│  │  │  6. Collect final LazyFrame → DataFrame                         │ │   │
│  │  │  7. Return sample data + schema + row count                     │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Engine Lifecycle

```
┌─────────────┐      spawn_engine()       ┌─────────────┐
│   (none)    │ ─────────────────────────►│    IDLE     │
└─────────────┘                           └──────┬──────┘
                                                 │
                                    execute()    │    60s idle timeout
                                                 ▼
                                          ┌─────────────┐
                                          │   RUNNING   │◄────────┐
                                          └──────┬──────┘         │
                                                 │                │
                              ┌──────────────────┴────────────────┘
                              │
                 completed/failed                          more work
                              │
                              ▼
                       ┌─────────────┐
                       │    IDLE     │───────────────────────────┘
                       └──────┬──────┘
                              │
                 shutdown_engine() or cleanup_idle_engines()
                              │
                              ▼
                       ┌─────────────┐
                       │ TERMINATED  │
                       └─────────────┘
```

---

## Storage Architecture

### Database Schema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE SCHEMA                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐         ┌─────────────────────────────┐   │
│  │        datasources          │         │         analyses            │   │
│  ├─────────────────────────────┤         ├─────────────────────────────┤   │
│  │ id          VARCHAR (PK)    │         │ id          VARCHAR (PK)    │   │
│  │ name        VARCHAR         │         │ name        VARCHAR         │   │
│  │ source_type VARCHAR         │         │ description VARCHAR NULL    │   │
│  │ config      JSON            │         │ pipeline_definition JSON    │   │
│  │ schema_cache JSON NULL      │         │ status      VARCHAR         │   │
│  │ created_at  DATETIME        │         │ created_at  DATETIME        │   │
│  └──────────────┬──────────────┘         │ updated_at  DATETIME        │   │
│                 │                         │ result_path VARCHAR NULL    │   │
│                 │                         │ thumbnail   VARCHAR NULL    │   │
│                 │                         └──────────────┬──────────────┘   │
│                 │                                        │                  │
│                 │    ┌───────────────────────────┐       │                  │
│                 │    │  analysis_datasources     │       │                  │
│                 │    ├───────────────────────────┤       │                  │
│                 └───►│ datasource_id VARCHAR (FK)│◄──────┘                  │
│                      │ analysis_id   VARCHAR (FK)│                          │
│                      ├───────────────────────────┤                          │
│                      │ PRIMARY KEY (datasource_id, analysis_id)             │
│                      │ ON DELETE CASCADE (both FKs)                         │
│                      └───────────────────────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### File Storage Layout

```
project_root/
└── backend/
    ├── database/
    │   └── app.db                    # SQLite database file
    │
    └── data/
        ├── uploads/                   # Raw data files
        │   ├── {uuid}.csv
        │   ├── {uuid}.parquet
        │   ├── {uuid}.json
        │   └── {uuid}.xlsx
        │
        └── results/                   # Computed results
            └── {analysis_id}.parquet  # Output in Parquet format
```

### JSON Schema: pipeline_definition

```json
{
  "steps": [
    {
      "id": "step-uuid-1",
      "type": "filter",
      "config": {
        "conditions": [
          {"column": "age", "operator": ">", "value": 18}
        ],
        "logic": "AND"
      },
      "depends_on": []
    },
    {
      "id": "step-uuid-2",
      "type": "select",
      "config": {
        "columns": ["name", "age", "city"]
      },
      "depends_on": ["step-uuid-1"]
    }
  ],
  "datasource_ids": ["ds-uuid-1"],
  "tabs": [
    {
      "id": "tab-uuid-1",
      "name": "Main Analysis",
      "type": "datasource",
      "parent_id": null,
      "datasource_id": "ds-uuid-1",
      "steps": [/* same as above */]
    }
  ]
}
```

---

## Communication Patterns

### REST API Communication

```
┌──────────────────┐                    ┌──────────────────┐
│     Frontend     │                    │     Backend      │
│   (Port 3000)    │                    │   (Port 8000)    │
└────────┬─────────┘                    └────────┬─────────┘
         │                                       │
         │  GET /api/v1/analysis                 │
         │──────────────────────────────────────►│
         │                                       │
         │  200 OK [Analysis[]]                  │
         │◄──────────────────────────────────────│
         │                                       │
         │  POST /api/v1/compute/execute         │
         │  {analysis_id: "..."}                 │
         │──────────────────────────────────────►│
         │                                       │
         │  200 OK {job_id: "...", status: ...}  │
         │◄──────────────────────────────────────│
         │                                       │
         │  GET /api/v1/compute/status/{job_id}  │  ┐
         │──────────────────────────────────────►│  │
         │                                       │  │ Polling
         │  200 OK {status: "running", ...}      │  │ (2s interval)
         │◄──────────────────────────────────────│  │
         │                                       │  │
         │  GET /api/v1/compute/status/{job_id}  │  │
         │──────────────────────────────────────►│  │
         │                                       │  │
         │  200 OK {status: "completed", ...}    │  ┘
         │◄──────────────────────────────────────│
         │                                       │
```

### IPC Communication (Multiprocessing)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IPC COMMUNICATION FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MAIN PROCESS                           SUBPROCESS                          │
│  ┌────────────────┐                    ┌────────────────┐                  │
│  │ Service Layer  │                    │ ComputeEngine  │                  │
│  └───────┬────────┘                    └───────┬────────┘                  │
│          │                                     │                            │
│          │  1. Create command                  │                            │
│          │  ┌─────────────────────────┐       │                            │
│          │  │ {                       │       │                            │
│          │  │   type: 'execute',      │       │                            │
│          │  │   job_id: 'job-123',    │       │                            │
│          │  │   datasource: {...},    │       │                            │
│          │  │   steps: [...]          │       │                            │
│          │  │ }                       │       │                            │
│          │  └─────────────────────────┘       │                            │
│          │                                     │                            │
│          │  2. command_queue.put(command)      │                            │
│          │────────────────────────────────────►│                            │
│          │                                     │                            │
│          │                                     │  3. Process pipeline       │
│          │                                     │     - Load data            │
│          │                                     │     - Apply operations     │
│          │                                     │     - Collect results      │
│          │                                     │                            │
│          │  4. result_queue.get()              │                            │
│          │◄────────────────────────────────────│                            │
│          │  ┌─────────────────────────┐       │                            │
│          │  │ {                       │       │                            │
│          │  │   job_id: 'job-123',    │       │                            │
│          │  │   status: 'completed',  │       │                            │
│          │  │   data: {               │       │                            │
│          │  │     sample_data: [...], │       │                            │
│          │  │     row_count: 1000,    │       │                            │
│          │  │     schema: {...}       │       │                            │
│          │  │   }                     │       │                            │
│          │  │ }                       │       │                            │
│          │  └─────────────────────────┘       │                            │
│          │                                     │                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Scalability Considerations

### Current Design Limitations

| Aspect | Current State | Limitation |
|--------|---------------|------------|
| **Concurrency** | Single machine | No horizontal scaling |
| **Database** | SQLite | Single writer, file-based |
| **Compute** | Local processes | Single machine CPU |
| **Storage** | Local filesystem | Single machine disk |
| **Sessions** | In-memory | Lost on restart |

### Potential Scaling Paths

1. **Database Migration**
   - Move from SQLite to PostgreSQL for concurrent writes
   - Enable connection pooling

2. **Compute Distribution**
   - Replace multiprocessing with distributed task queue (Celery, RQ)
   - Enable horizontal scaling of compute workers

3. **Storage Migration**
   - Move file storage to object storage (S3, MinIO)
   - Enable distributed file access

4. **Caching Layer**
   - Add Redis for session/job state
   - Enable multi-instance deployment

5. **Load Balancing**
   - Add reverse proxy (nginx)
   - Enable multiple backend instances

### Current Optimization Points

| Optimization | Implementation |
|--------------|----------------|
| **Lazy Evaluation** | Polars LazyFrame delays computation |
| **Schema Caching** | Database-level schema cache |
| **Engine Pooling** | Reuse compute engines per analysis |
| **Query Caching** | TanStack Query 5-min stale time |
| **Client Schema Calc** | No API call for schema preview |

---

## See Also

- [Design Patterns](./design-patterns.md) - Pattern implementations
- [Data Flow](./data-flow.md) - Detailed data flow documentation
- [Technology Decisions](./technology-decisions.md) - Architecture Decision Records
