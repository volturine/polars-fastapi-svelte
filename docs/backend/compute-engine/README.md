# Compute Engine Documentation

Complete documentation for the Polars compute engine subsystem.

## Overview

The compute engine handles data transformation execution using isolated multiprocessing. Each analysis gets its own subprocess to ensure stability and enable parallel execution.

## Contents

| Document | Description |
|----------|-------------|
| [Architecture](./architecture.md) | Engine architecture and design |
| [Operations](./operations.md) | Supported Polars operations |
| [Pipeline Execution](./pipeline-execution.md) | Execution flow and DAG processing |

## Key Components

### ProcessManager (Singleton)

Manages the pool of compute engines:

```python
class ProcessManager:
    _instance = None
    _engines: dict[str, EngineInfo]

    def spawn_engine(analysis_id) -> EngineInfo
    def shutdown_engine(analysis_id) -> bool
    def cleanup_idle_engines() -> list[str]
    def shutdown_all() -> None
```

### PolarsComputeEngine (Subprocess)

Executes Polars transformations in isolation:

```python
class PolarsComputeEngine:
    command_queue: Queue  # Input commands
    result_queue: Queue   # Output results
    process: Process      # Subprocess handle

    def execute(job_id, config, steps) -> str
    def get_result(timeout=1.0) -> dict | None
    def shutdown() -> None
```

### StepConverter

Converts frontend format to backend format:

```python
def convert_step(step: dict) -> dict
def convert_filter_config(step) -> dict
def convert_groupby_config(step) -> dict
# ... more converters
```

## Engine Lifecycle

```
                    spawn_engine()
    (none) ─────────────────────────► IDLE
                                        │
                        execute()       │    60s timeout
                                        ▼
                                     RUNNING ◄────┐
                                        │         │
                        completed       │    more work
                                        ▼         │
                                      IDLE ───────┘
                                        │
                        shutdown()      │
                                        ▼
                                   TERMINATED
```

## IPC Communication

```
MAIN PROCESS                    SUBPROCESS

service.py
    │
    ▼
ProcessManager
    │
    │ command_queue.put({
    │   type: 'execute',
    │   job_id: '...',
    │   config: {...},
    │   steps: [...]
    │ })
    │
    └──────────────────────────► Event Loop
                                      │
                                      ▼
                                 _execute_pipeline()
                                      │
                                      ▼
    ◄──────────────────────────── result_queue.put({
                                      job_id: '...',
                                      status: 'completed',
                                      data: {...}
                                   })
```

## Supported Operations

20+ Polars operations including:

| Category | Operations |
|----------|------------|
| **Selection** | select, drop, rename |
| **Filtering** | filter, limit, sample, topk |
| **Aggregation** | group_by, value_counts |
| **Reshaping** | pivot, unpivot, explode |
| **Joins** | join (self-join) |
| **Transformation** | sort, deduplicate, fill_null |
| **String** | string_transform (20+ methods) |
| **Time Series** | timeseries operations |
| **Expressions** | with_columns, cast, expression |

## Configuration

```python
# core/config.py
compute_timeout: int = 300  # 5 minutes
job_ttl: int = 3600         # 1 hour cleanup
```

## See Also

- [Architecture](./architecture.md) - Detailed architecture
- [Operations](./operations.md) - All operations
- [Compute Module](../modules/compute.md) - Routes and service
