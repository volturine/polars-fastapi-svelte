# Compute Module

Complete documentation for the Compute module, which handles pipeline execution, engine lifecycle management, and job tracking.

## Overview

The Compute module orchestrates the execution of data transformation pipelines using isolated multiprocessing engines. It manages the lifecycle of compute engines, tracks job status, and provides preview functionality.

**Location**: `backend/modules/compute/`

## Files

| File | Purpose |
|------|---------|
| `engine.py` | `PolarsComputeEngine` - subprocess worker |
| `manager.py` | `ProcessManager` - singleton engine pool |
| `step_converter.py` | Frontend → backend format conversion |
| `schemas.py` | Pydantic schemas |
| `routes.py` | FastAPI route handlers |
| `service.py` | Job tracking and coordination |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPUTE ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MAIN PROCESS (FastAPI)                                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  routes.py → service.py → ProcessManager (singleton)                   │ │
│  │                               │                                        │ │
│  │                    ┌──────────┴──────────┐                            │ │
│  │                    ▼                     ▼                            │ │
│  │            ┌─────────────┐       ┌─────────────┐                      │ │
│  │            │ EngineInfo  │       │ EngineInfo  │  (per analysis)      │ │
│  │            │ analysis-1  │       │ analysis-2  │                      │ │
│  │            └──────┬──────┘       └──────┬──────┘                      │ │
│  │                   │                     │                             │ │
│  └───────────────────┼─────────────────────┼─────────────────────────────┘ │
│                      │                     │                               │
│           command_queue / result_queue (IPC)                               │
│                      │                     │                               │
│  ┌───────────────────▼─────────────────────▼─────────────────────────────┐ │
│  │                    SUBPROCESSES (PolarsComputeEngine)                  │ │
│  │                                                                        │ │
│  │  ┌────────────────────┐       ┌────────────────────┐                  │ │
│  │  │  Engine Process 1  │       │  Engine Process 2  │                  │ │
│  │  │                    │       │                    │                  │ │
│  │  │  while True:       │       │  while True:       │                  │ │
│  │  │    cmd = queue.get │       │    cmd = queue.get │                  │ │
│  │  │    result = exec() │       │    result = exec() │                  │ │
│  │  │    queue.put(res)  │       │    queue.put(res)  │                  │ │
│  │  └────────────────────┘       └────────────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Schemas

### ComputeExecuteSchema

```python
class ComputeExecuteSchema(BaseModel):
    analysis_id: str
    execute_mode: str = 'full'  # 'full' or 'preview'
    step_id: str | None = None
```

### ComputeStatusSchema

```python
class ComputeStatusSchema(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed, cancelled
    progress: float = 0.0  # 0.0 to 1.0
    current_step: str | None = None
    error_message: str | None = None
    process_id: int | None = None
```

### ComputeResultSchema

```python
class ComputeResultSchema(BaseModel):
    job_id: str
    status: str
    data: dict | None = None  # {sample_data, row_count, schema}
    error: str | None = None
```

### StepPreviewRequest

```python
class StepPreviewRequest(BaseModel):
    datasource_id: str
    pipeline_steps: list[dict]
    target_step_id: str
    row_limit: int = 1000
    page: int = 1
```

### StepPreviewResponse

```python
class StepPreviewResponse(BaseModel):
    step_id: str
    columns: list[str]
    data: list[dict]
    total_rows: int
    page: int
    page_size: int
```

### EngineStatusSchema

```python
class EngineStatusSchema(BaseModel):
    analysis_id: str
    status: str  # idle, running, error, terminated
    process_id: int | None = None
    last_activity: datetime | None = None
```

### Status Enums

```python
class JobStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class EngineStatus(str, Enum):
    IDLE = 'idle'
    RUNNING = 'running'
    ERROR = 'error'
    TERMINATED = 'terminated'
```

---

## Routes

### POST /api/v1/compute/execute

Execute an analysis pipeline.

**Request**:
```json
{
  "analysis_id": "analysis-uuid-123"
}
```

**Response** (200 OK):
```json
{
  "job_id": "job-uuid-456",
  "status": "pending",
  "progress": 0.0,
  "current_step": null,
  "error_message": null,
  "process_id": 12345
}
```

### POST /api/v1/compute/preview

Preview step result with pagination.

**Request**:
```json
{
  "datasource_id": "ds-uuid-123",
  "pipeline_steps": [
    {"id": "step-1", "type": "filter", "config": {...}}
  ],
  "target_step_id": "step-1",
  "row_limit": 100,
  "page": 1
}
```

**Response** (200 OK):
```json
{
  "step_id": "step-1",
  "columns": ["id", "name", "age"],
  "data": [
    {"id": 1, "name": "Alice", "age": 30},
    ...
  ],
  "total_rows": 5000,
  "page": 1,
  "page_size": 100
}
```

### GET /api/v1/compute/status/{job_id}
 
Get job execution status.

**Response** (200 OK):
```json
{
  "job_id": "job-uuid-456",
  "status": "running",
  "progress": 0.5,
  "current_step": "Filter",
  "error_message": null,
  "process_id": 12345
}
```
 
### GET /api/v1/compute/result/{job_id}
 
Get completed job result.

**Response** (200 OK):
```json
{
  "job_id": "job-uuid-456",
  "status": "completed",
  "data": {
    "sample_data": [...],
    "row_count": 5000,
    "schema": {"id": "Int64", "name": "String"}
  },
  "error": null
}
```
 
### GET /api/v1/compute/engines
 
List active engines and their status (includes `current_job_id`).

**Response** (200 OK):
```json
{
  "engines": [
    {
      "analysis_id": "analysis-uuid-123",
      "status": "running",
      "process_id": 12345,
      "last_activity": "2024-01-15T10:30:00Z",
      "current_job_id": "job-uuid-456"
    }
  ],
  "total": 1
}
```
 
### POST /api/v1/compute/export
 
Export pipeline output to CSV, Parquet, JSON, or NDJSON. Destination can be browser download or filesystem `data/exports`.

**Request**:
```json
{
  "datasource_id": "ds-uuid-123",
  "pipeline_steps": [{"id": "step-1", "type": "select", "config": {}}],
  "target_step_id": "step-1",
  "format": "csv",
  "filename": "export",
  "destination": "download"
}
```

**Response** (200 OK):
- `download` → file stream with `Content-Disposition`
- `filesystem` → JSON body with saved file path
 
### DELETE /api/v1/compute/{job_id}
 
Cancel running job.

**Response** (200 OK):
```json
{
  "message": "Job cancelled"
}
```
 
### DELETE /api/v1/compute/{job_id}/cleanup
 
Clean up job from memory.

**Response** (200 OK):
```json
{
  "message": "Job cleaned up"
}
```
 
### POST /api/v1/compute/engine/spawn/{analysis_id}
 
Spawn or get existing compute engine.

**Response** (200 OK):
```json
{
  "analysis_id": "analysis-uuid-123",
  "status": "idle",
  "process_id": 12345,
  "last_activity": "2024-01-15T10:30:00Z"
}
```
 
### POST /api/v1/compute/engine/keepalive/{analysis_id}
 
Send keepalive ping to prevent timeout.

**Response** (200 OK): `EngineStatusSchema`
 
### GET /api/v1/compute/engine/status/{analysis_id}
 
Get engine status.

**Response** (200 OK): `EngineStatusSchema`
 
### DELETE /api/v1/compute/engine/{analysis_id}
 
Shutdown engine.

**Response** (200 OK):
```json
{
  "message": "Engine shutdown"
}
```


---

## ProcessManager

Singleton that manages the pool of compute engines.

### Class Structure

```python
class ProcessManager:
    _instance: 'ProcessManager | None' = None
    _engines: dict[str, EngineInfo]

    def __new__(cls) -> 'ProcessManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engines = {}
        return cls._instance
```

### Methods

#### spawn_engine

```python
def spawn_engine(self, analysis_id: str) -> EngineInfo
```

Creates or returns existing engine for analysis.

**Logic**:
1. Check if engine exists for analysis_id
2. If exists, touch (update activity) and return
3. If not, create new PolarsComputeEngine
4. Start subprocess
5. Store in _engines dict
6. Return EngineInfo

#### get_or_create_engine

```python
def get_or_create_engine(self, analysis_id: str) -> EngineInfo
```

Alias for spawn_engine.

#### keepalive

```python
def keepalive(self, analysis_id: str) -> EngineInfo | None
```

Updates last_activity timestamp.

#### get_engine_status

```python
def get_engine_status(self, analysis_id: str) -> EngineStatusSchema | None
```

Returns current engine status.

#### shutdown_engine

```python
def shutdown_engine(self, analysis_id: str) -> bool
```

Gracefully shuts down engine.

**Shutdown sequence**:
1. Send shutdown command via queue
2. Wait for process (timeout: 5 seconds)
3. If still alive, terminate
4. If still alive, kill
5. Remove from _engines dict

#### cleanup_idle_engines

```python
def cleanup_idle_engines(self) -> list[str]
```

Shuts down engines idle for longer than `settings.engine_idle_timeout` seconds. Engines with running jobs are skipped.

#### shutdown_all

```python
def shutdown_all(self) -> None
```

Shuts down all engines (called on app shutdown).

### EngineInfo

```python
class EngineInfo:
    engine: PolarsComputeEngine
    last_activity: datetime
    status: EngineStatus

    def is_idle_for(self, seconds: int) -> bool:
        return (datetime.now() - self.last_activity).seconds > seconds

    def touch(self) -> None:
        self.last_activity = datetime.now()
```

---

## PolarsComputeEngine

Subprocess-based engine that executes Polars transformations.

### Class Structure

```python
class PolarsComputeEngine:
    def __init__(self, analysis_id: str):
        self.analysis_id = analysis_id
        self.command_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.process: multiprocessing.Process | None = None
```

### Methods

#### start

```python
def start(self) -> None
```

Starts the subprocess.

```python
self.process = multiprocessing.Process(
    target=PolarsComputeEngine._run_compute,
    args=(self.command_queue, self.result_queue)
)
self.process.start()
```

#### execute

```python
def execute(
    self,
    job_id: str,
    datasource_config: dict,
    pipeline_steps: list[dict]
) -> str
```

Queues execution command.

```python
command = {
    'type': 'execute',
    'job_id': job_id,
    'datasource_config': datasource_config,
    'pipeline_steps': pipeline_steps
}
self.command_queue.put(command)
return job_id
```

#### get_result

```python
def get_result(self, timeout: float = 1.0) -> dict | None
```

Non-blocking result retrieval.

```python
try:
    return self.result_queue.get(timeout=timeout)
except queue.Empty:
    return None
```

#### shutdown

```python
def shutdown(self) -> None
```

Graceful shutdown with escalation.

### Static Method: _run_compute

```python
@staticmethod
def _run_compute(command_queue, result_queue):
    """Main subprocess loop."""
    while True:
        command = command_queue.get()

        if command['type'] == 'shutdown':
            break

        if command['type'] == 'execute':
            try:
                result = PolarsComputeEngine._execute_pipeline(
                    command['datasource_config'],
                    command['pipeline_steps']
                )
                result_queue.put({
                    'job_id': command['job_id'],
                    'status': JobStatus.COMPLETED,
                    'data': result
                })
            except Exception as e:
                result_queue.put({
                    'job_id': command['job_id'],
                    'status': JobStatus.FAILED,
                    'error': str(e)
                })
```

### Static Method: _execute_pipeline

```python
@staticmethod
def _execute_pipeline(
    datasource_config: dict,
    pipeline_steps: list[dict]
) -> dict
```

Executes the pipeline.

**Steps**:
1. Load datasource as LazyFrame
2. Convert frontend steps to backend format
3. Build dependency graph
4. Topological sort
5. Apply operations sequentially
6. Collect final result
7. Return schema, row_count, sample_data

---

## Step Converter

Converts frontend step format to backend execution format.

### Conversion Example

**Frontend**:
```json
{
  "id": "step-123",
  "type": "groupby",
  "config": {
    "groupBy": ["category"],
    "aggregations": [
      {"column": "sales", "function": "sum", "alias": "total"}
    ]
  }
}
```

**Backend**:
```json
{
  "name": "step-123",
  "operation": "group_by",
  "params": {
    "group_by": ["category"],
    "aggregations": [
      {"column": "sales", "function": "sum", "alias": "total"}
    ]
  }
}
```

### Converter Functions

| Function | Operation | Notes |
|----------|-----------|-------|
| `convert_filter_config` | filter | Handles conditions, logic |
| `convert_select_config` | select | Column selection |
| `convert_groupby_config` | group_by | camelCase → snake_case |
| `convert_join_config` | join | Both naming conventions |
| `convert_pivot_config` | pivot | aggregateFunction fix |
| `convert_sort_config` | sort | Multi-column support |
| `convert_fillnull_config` | fill_null | Strategy normalization |
| `convert_rename_config` | rename | column_mapping fix |
| `convert_passthrough` | * | Direct pass-through |

---

## Service Functions

### execute_analysis

```python
async def execute_analysis(
    session: AsyncSession,
    datasource_id: str,
    pipeline_steps: list[dict]
) -> ComputeJob
```

Starts pipeline execution.

### preview_step

```python
async def preview_step(
    session: AsyncSession,
    datasource_id: str,
    pipeline_steps: list[dict],
    target_step_id: str,
    row_limit: int = 1000,
    page: int = 1
) -> StepPreviewResponse
```

Previews step result with pagination.

### Job Tracking

In-memory tracking:

```python
_job_status: dict[str, dict] = {}
_job_results: dict[str, dict] = {}
```

Job cleanup happens when engines are terminated via `cleanup_jobs_for_engine(analysis_id)`.

---

## Supported Operations
 
See [Operations Reference](../../reference/polars-operations.md) for full list:
 
- filter, select, drop, rename
- sort, limit, sample, topk
- group_by, join, pivot, unpivot
- deduplicate, fill_null, explode
- string_transform, timeseries
- with_columns, cast, expression
- null_count, value_counts
- export (passthrough trigger for download/save)
 
---
 
## See Also


- [Compute Engine Architecture](../compute-engine/README.md)
- [Operations Reference](../../reference/polars-operations.md)
- [DataSource Module](./datasource.md)
