# Compute Engine Architecture

Detailed architecture documentation for the Polars compute engine subsystem.

## Overview

The compute engine uses isolated multiprocessing to execute Polars transformations. Each analysis gets its own subprocess, providing process isolation, crash recovery, and parallel execution capability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MAIN PROCESS                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                        FastAPI Application                        │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │   │
│  │  │ /execute     │  │ /job/{id}    │  │ /engine/status       │   │   │
│  │  │ POST         │  │ GET          │  │ GET                  │   │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │   │
│  │         │                 │                     │               │   │
│  │         ▼                 ▼                     ▼               │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │                    ComputeService                        │   │   │
│  │  │  - execute_pipeline()                                    │   │   │
│  │  │  - get_job_status()                                      │   │   │
│  │  │  - cleanup_jobs()                                        │   │   │
│  │  └────────────────────────┬─────────────────────────────────┘   │   │
│  │                           │                                     │   │
│  │                           ▼                                     │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │                  ProcessManager (Singleton)              │   │   │
│  │  │  ┌───────────────────────────────────────────────────┐   │   │   │
│  │  │  │  _engines: dict[str, EngineInfo]                  │   │   │   │
│  │  │  │                                                    │   │   │   │
│  │  │  │  analysis_1 ─► EngineInfo(engine, last_activity)  │   │   │   │
│  │  │  │  analysis_2 ─► EngineInfo(engine, last_activity)  │   │   │   │
│  │  │  │  analysis_3 ─► EngineInfo(engine, last_activity)  │   │   │   │
│  │  │  └───────────────────────────────────────────────────┘   │   │   │
│  │  └────────────────────────┬─────────────────────────────────┘   │   │
│  │                           │                                     │   │
│  └───────────────────────────┼─────────────────────────────────────┘   │
│                              │                                         │
│                              │ IPC via Queues                          │
│                              │                                         │
├──────────────────────────────┼─────────────────────────────────────────┤
│                              │                                         │
│  ┌───────────────────────────┴─────────────────────────────────────┐   │
│  │                   SUBPROCESS POOL                                │   │
│  │                                                                  │   │
│  │  ┌────────────────────────────────────────────────────────┐     │   │
│  │  │         PolarsComputeEngine (analysis_1)               │     │   │
│  │  │  ┌──────────────┐      ┌──────────────┐               │     │   │
│  │  │  │command_queue │      │ result_queue │               │     │   │
│  │  │  │   (input)    │      │   (output)   │               │     │   │
│  │  │  └──────┬───────┘      └──────▲───────┘               │     │   │
│  │  │         │                     │                        │     │   │
│  │  │         ▼                     │                        │     │   │
│  │  │  ┌────────────────────────────┴───────────────────┐   │     │   │
│  │  │  │              _run_compute() loop               │   │     │   │
│  │  │  │                                                │   │     │   │
│  │  │  │  1. command_queue.get()                        │   │     │   │
│  │  │  │  2. _execute_pipeline()                        │   │     │   │
│  │  │  │  3. result_queue.put(result)                   │   │     │   │
│  │  │  └────────────────────────────────────────────────┘   │     │   │
│  │  └────────────────────────────────────────────────────────┘     │   │
│  │                                                                  │   │
│  │  ┌────────────────────────────────────────────────────────┐     │   │
│  │  │         PolarsComputeEngine (analysis_2)               │     │   │
│  │  │                    ...                                 │     │   │
│  │  └────────────────────────────────────────────────────────┘     │   │
│  │                                                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Components

### ProcessManager (Singleton)

Central manager for all compute engines.

```python
class ProcessManager:
    _instance: 'ProcessManager | None' = None
    _engines: dict[str, EngineInfo]
    _idle_timeout: int = 60  # seconds

    def __new__(cls) -> 'ProcessManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engines = {}
        return cls._instance
```

**Responsibilities**:
- Maintains engine pool
- Spawns/shuts down engines
- Tracks engine activity
- Cleans up idle engines

### EngineInfo

Wrapper tracking engine state and activity.

```python
class EngineInfo:
    def __init__(self, engine: PolarsComputeEngine):
        self.engine = engine
        self.last_activity = datetime.now(UTC)
        self.status = EngineStatus.IDLE

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now(UTC)

    def is_idle_for(self, seconds: int) -> bool:
        """Check if engine has been idle for more than N seconds."""
        elapsed = (datetime.now(UTC) - self.last_activity).total_seconds()
        return elapsed > seconds
```

### PolarsComputeEngine

The actual compute subprocess handler.

```python
class PolarsComputeEngine:
    def __init__(self, analysis_id: str):
        self.analysis_id = analysis_id
        self.process: mp.Process | None = None
        self.command_queue: mp.Queue = mp.Queue()
        self.result_queue: mp.Queue = mp.Queue()
        self.is_running = False
        self.current_job_id: str | None = None
```

**Key Methods**:
- `start()` - Launch subprocess
- `execute()` - Submit job to queue
- `get_result()` - Poll result queue
- `shutdown()` - Graceful termination

## IPC Communication

### Queue-Based Protocol

```
MAIN PROCESS                              SUBPROCESS

service.py
    │
    ▼
ProcessManager.spawn_engine()
    │
    ▼
PolarsComputeEngine
    │
    │  command_queue.put({
    │      type: 'execute',
    │      job_id: 'uuid',
    │      datasource_config: {...},
    │      pipeline_steps: [...]
    │  })
    │
    └─────────────────────────────────► _run_compute()
                                              │
                                              ▼
                                        _execute_pipeline()
                                              │
                                              │ progress updates
                                              │
    ◄─────────────────────────────────────────┤
                                              │
    result_queue.get()                        │
         │                                    ▼
         ▼                              result_queue.put({
    return to client                        job_id: '...',
                                            status: 'completed',
                                            data: {...}
                                        })
```

### Message Types

**Command Messages** (main → subprocess):

```python
# Execute command
{
    'type': 'execute',
    'job_id': 'uuid-string',
    'datasource_config': {
        'source_type': 'file',
        'file_path': '/path/to/data.csv',
        'file_type': 'csv'
    },
    'pipeline_steps': [
        {'id': 'step-1', 'type': 'filter', 'config': {...}},
        {'id': 'step-2', 'type': 'select', 'config': {...}}
    ],
    'timeout': 300
}

# Shutdown command
{
    'type': 'shutdown'
}
```

**Result Messages** (subprocess → main):

```python
# Progress update
{
    'job_id': 'uuid-string',
    'status': 'running',
    'progress': 0.5,
    'current_step': 'Applying filter',
    'error': None
}

# Completion
{
    'job_id': 'uuid-string',
    'status': 'completed',
    'progress': 1.0,
    'current_step': None,
    'data': {
        'schema': {'col1': 'Int64', 'col2': 'String'},
        'row_count': 1000,
        'sample_data': [...]
    },
    'error': None
}

# Error
{
    'job_id': 'uuid-string',
    'status': 'failed',
    'progress': 0.0,
    'current_step': None,
    'error': 'Filter column "foo" not found'
}
```

## Engine Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                        Engine States                             │
└─────────────────────────────────────────────────────────────────┘

                     spawn_engine()
      (none) ─────────────────────────────────► IDLE
                                                  │
                                                  │ execute()
                                                  ▼
                                               RUNNING
                                                  │
                         ┌────────────────────────┼────────────────────────┐
                         │                        │                        │
                         ▼                        ▼                        ▼
                    completed                   failed                 more work
                         │                        │                        │
                         │                        │                        │
                         ▼                        ▼                        │
                       IDLE ◄─────────────────────┘◄───────────────────────┘
                         │
                         │ idle_timeout (60s) OR shutdown()
                         ▼
                    TERMINATED
```

### State Transitions

| From | Event | To |
|------|-------|-----|
| none | `spawn_engine()` | IDLE |
| IDLE | `execute()` | RUNNING |
| RUNNING | job completed | IDLE |
| RUNNING | job failed | IDLE |
| IDLE | 60s timeout | TERMINATED |
| IDLE | `shutdown()` | TERMINATED |
| RUNNING | `shutdown()` | TERMINATED |

## Lazy Evaluation

The engine uses Polars LazyFrame for memory efficiency.

```python
@staticmethod
def _execute_pipeline(
    datasource_config: dict,
    pipeline_steps: list[dict],
    job_id: str,
    result_queue: mp.Queue,
) -> dict:
    # Load as LazyFrame - no data loaded yet
    lf = PolarsComputeEngine._load_datasource(datasource_config)

    # Apply transformations - still lazy
    for step in ordered_steps:
        lf = PolarsComputeEngine._apply_step(lf, step)

    # Only collect at the very end
    df = lf.collect()

    return {
        'schema': {col: str(dtype) for col, dtype in df.schema.items()},
        'row_count': len(df),
        'sample_data': df.head(5000).to_dicts(),
    }
```

**Benefits**:
- Memory efficient: Only loads needed data
- Query optimization: Polars optimizes the entire pipeline
- Predicate pushdown: Filters applied at scan time

## DAG Processing

Pipeline steps form a Directed Acyclic Graph (DAG).

```python
# Build dependency graph
dependency_map: dict[str, str | None] = {}
for step_id, step in step_map.items():
    deps = step.get('depends_on') or []
    if len(deps) == 0:
        dependency_map[step_id] = None
    else:
        dependency_map[step_id] = deps[0]

# Topological sort (Kahn's algorithm)
queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
ordered_steps: list[dict] = []
while queue:
    current_id = queue.pop(0)
    ordered_steps.append(step_map[current_id])
    for child_id in dependents.get(current_id, []):
        in_degree[child_id] -= 1
        if in_degree[child_id] == 0:
            queue.append(child_id)

# Cycle detection
if len(ordered_steps) != len(step_map):
    raise ValueError('Pipeline contains a cycle')
```

## Error Handling

### Subprocess Crash Recovery

```python
def execute(self, datasource_config: dict, pipeline_steps: list[dict], timeout: int = 300) -> str:
    if not self.is_running:
        self.start()  # Auto-restart if crashed

    command = {...}
    self.command_queue.put(command)
    return job_id
```

### Graceful Shutdown

```python
def shutdown(self) -> None:
    # Request graceful shutdown
    self.command_queue.put({'type': 'shutdown'})

    if self.process and self.process.is_alive():
        # Wait for graceful exit
        self.process.join(timeout=5)

        # Terminate if still running
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=2)

        # Kill if still running
        if self.process.is_alive():
            self.process.kill()

    self.is_running = False
```

## Configuration

```python
# core/config.py
compute_timeout: int = 300  # 5 minutes max per job
job_ttl: int = 3600         # 1 hour job result retention

# modules/compute/manager.py
_idle_timeout: int = 60     # Engine idle timeout
```

## See Also

- [Operations](./operations.md) - Supported Polars operations
- [Pipeline Execution](./pipeline-execution.md) - Execution flow details
- [Compute Module](../modules/compute.md) - Routes and service
