# Pipeline Execution

Detailed documentation of the pipeline execution flow.

## Overview

Pipeline execution follows a multi-phase process: step conversion, DAG construction, topological sorting, lazy transformation, and final collection.

## Execution Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE EXECUTION FLOW                              │
└──────────────────────────────────────────────────────────────────────────────┘

 Frontend Steps                    Step Conversion                 Backend Steps
 ┌────────────┐                   ┌──────────────┐                ┌────────────┐
 │ {          │   convert_step    │              │                │ {          │
 │   id,      │ ─────────────────►│ StepConverter│───────────────►│   operation│
 │   type,    │                   │              │                │   params   │
 │   config   │                   └──────────────┘                │   name     │
 │ }          │                                                   │ }          │
 └────────────┘                                                   └────────────┘
                                                                        │
                                                                        ▼
                                                              ┌─────────────────┐
                                                              │ DAG Construction│
                                                              │  - Build graph  │
                                                              │  - Check cycles │
                                                              └────────┬────────┘
                                                                       │
                                                                       ▼
                                                              ┌─────────────────┐
                                                              │Topological Sort │
                                                              │ (Kahn's algo)   │
                                                              └────────┬────────┘
                                                                       │
                                                                       ▼
                                                              ┌─────────────────┐
                                                              │ Load Datasource │
                                                              │   → LazyFrame   │
                                                              └────────┬────────┘
                                                                       │
           ┌───────────────────────────────────────────────────────────┘
           │
           ▼
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │   Step 1     │────►│   Step 2     │────►│   Step N     │
    │ _apply_step  │     │ _apply_step  │     │ _apply_step  │
    │  (lazy)      │     │  (lazy)      │     │  (lazy)      │
    └──────────────┘     └──────────────┘     └──────────────┘
                                                     │
                                                     ▼
                                              ┌──────────────┐
                                              │   .collect() │
                                              │  (execute)   │
                                              └──────────────┘
                                                     │
                                                     ▼
                                              ┌──────────────┐
                                              │    Result    │
                                              │   schema     │
                                              │   row_count  │
                                              │   sample     │
                                              └──────────────┘
```

## Phase 1: Step Conversion

Frontend step format is converted to backend format.

### Frontend Format

```python
{
    'id': 'step-uuid',
    'type': 'filter',
    'config': {
        'conditions': [
            {'column': 'age', 'operator': '>', 'value': 18}
        ],
        'logic': 'AND'
    },
    'depends_on': ['previous-step-id']
}
```

### Backend Format

```python
{
    'operation': 'filter',
    'params': {
        'conditions': [
            {'column': 'age', 'operator': '>', 'value': 18}
        ],
        'logic': 'AND'
    },
    'name': 'Filter'
}
```

### Conversion Logic

```python
# modules/compute/step_converter.py
def convert_step_format(step: dict) -> dict:
    step_type = step.get('type')
    config = step.get('config', {})

    if step_type == 'filter':
        return convert_filter_config(config)
    elif step_type == 'select':
        return convert_select_config(config)
    # ... more converters
```

## Phase 2: DAG Construction

Steps form a Directed Acyclic Graph based on dependencies.

### Input

```python
steps = [
    {'id': 'a', 'depends_on': []},
    {'id': 'b', 'depends_on': ['a']},
    {'id': 'c', 'depends_on': ['a']},
    {'id': 'd', 'depends_on': ['b', 'c']},  # Error: multiple deps
]
```

### DAG Visualization

```
    ┌───┐
    │ a │  (root - no dependencies)
    └─┬─┘
      │
      ▼
    ┌───┐
    │ b │
    └─┬─┘
      │
      ▼
    ┌───┐
    │ c │
    └───┘
```

### Cycle Detection

```python
# If ordered_steps != all steps, there's a cycle
if len(ordered_steps) != len(step_map):
    raise ValueError('Pipeline contains a cycle')
```

**Error Example**:
```
a → b → c → a  (cycle detected)
```

## Phase 3: Topological Sort

Kahn's algorithm ensures correct execution order.

```python
# Build in-degree map
in_degree: dict[str, int] = {step_id: 0 for step_id in step_map}
for step_id in step_map:
    deps = step.get('depends_on') or []
    for dep_id in deps:
        in_degree[step_id] += 1

# Process nodes with no dependencies first
queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
ordered_steps: list[dict] = []

while queue:
    current_id = queue.pop(0)
    ordered_steps.append(step_map[current_id])

    # Reduce in-degree for dependent steps
    for child_id in dependents.get(current_id, []):
        in_degree[child_id] -= 1
        if in_degree[child_id] == 0:
            queue.append(child_id)
```

### Execution Order Example

```
Input dependencies:
  a → []
  b → [a]
  c → [b]

Execution order: [a, b, c]
```

## Phase 4: Data Loading

Datasource is loaded as LazyFrame.

```python
@staticmethod
def _load_datasource(config: dict) -> pl.LazyFrame:
    source_type = config.get('source_type', 'file')

    if source_type == 'file':
        file_path = config['file_path']
        file_type = config['file_type']

        if file_type == 'csv':
            return pl.scan_csv(file_path)
        elif file_type == 'parquet':
            return pl.scan_parquet(file_path)
        elif file_type == 'json':
            return pl.scan_ndjson(file_path)
        elif file_type == 'excel':
            return pl.read_excel(file_path).lazy()

    elif source_type == 'database':
        connection_string = config['connection_string']
        query = config['query']
        return pl.read_database(query, connection_string).lazy()
```

### Lazy vs Eager Loading

| File Type | Method | Lazy? |
|-----------|--------|-------|
| CSV | `scan_csv()` | Yes |
| Parquet | `scan_parquet()` | Yes |
| NDJSON | `scan_ndjson()` | Yes |
| Excel | `read_excel().lazy()` | Eager then lazy |
| Database | `read_database().lazy()` | Eager then lazy |

## Phase 5: Transformation Chain

Each step transforms the LazyFrame.

```python
schema_map: dict[str, pl.LazyFrame] = {}

for idx, step in enumerate(ordered_steps):
    backend_step = convert_step_format(step)

    # Get parent frame (either base or from dependency)
    step_id = step.get('id')
    parent_id = dependency_map.get(step_id)

    if parent_id is not None:
        parent_frame = schema_map.get(parent_id)
    else:
        parent_frame = lf  # Base LazyFrame

    # Apply transformation
    schema_map[step_id] = PolarsComputeEngine._apply_step(parent_frame, backend_step)

    # Report progress
    progress = (idx + 1) / total_steps
    result_queue.put({
        'job_id': job_id,
        'status': JobStatus.RUNNING,
        'progress': progress,
        'current_step': backend_step.get('name'),
        'error': None,
    })
```

### LazyFrame Chain

```python
# Each transformation returns a new LazyFrame
lf = pl.scan_csv("data.csv")           # LazyFrame
lf = lf.filter(pl.col("age") > 18)     # Still LazyFrame
lf = lf.select(["name", "age"])        # Still LazyFrame
lf = lf.sort("name")                   # Still LazyFrame
# No data processed yet!
```

## Phase 6: Collection

Data is only materialized at the end.

```python
# Get the last step's LazyFrame
last_step = ordered_steps[-1] if ordered_steps else None
if last_step:
    last_id = last_step.get('id')
    last_frame = schema_map.get(last_id)
    df = last_frame.collect()  # <-- DATA PROCESSED HERE
else:
    df = lf.collect()

# Build result
output = {
    'schema': {col: str(dtype) for col, dtype in df.schema.items()},
    'row_count': len(df),
    'sample_data': df.head(5000).to_dicts(),
}
```

### Polars Query Optimization

Before collection, Polars optimizes the query:

```
Original:                          Optimized:
scan_csv()                         scan_csv(
  │                                  projection=["name", "age"],
  ▼                                  predicate=col("age") > 18
filter(age > 18)                   )
  │                                  │
  ▼                                  ▼
select([name, age])                sort("name")
  │
  ▼
sort("name")
```

**Optimizations Applied**:
- Predicate pushdown (filter at scan time)
- Projection pushdown (only read needed columns)
- Operation fusion (combine compatible operations)

## Progress Reporting

Progress is reported via the result queue.

```python
# Initial status
result_queue.put({
    'job_id': job_id,
    'status': JobStatus.RUNNING,
    'progress': 0.0,
    'current_step': 'Loading data',
    'error': None,
})

# Per-step progress
for idx, step in enumerate(ordered_steps):
    progress = (idx + 1) / total_steps
    result_queue.put({
        'job_id': job_id,
        'status': JobStatus.RUNNING,
        'progress': progress,
        'current_step': step_name,
        'error': None,
    })

# Completion
result_queue.put({
    'job_id': job_id,
    'status': JobStatus.COMPLETED,
    'progress': 1.0,
    'current_step': None,
    'data': result_data,
    'error': None,
})
```

## Error Handling

### Step Conversion Errors

```python
try:
    backend_step = convert_step_format(step)
except Exception as e:
    result_queue.put({
        'job_id': job_id,
        'status': JobStatus.FAILED,
        'progress': 0.0,
        'error': f'Step conversion failed: {str(e)}',
    })
    raise
```

### Execution Errors

```python
try:
    result_data = PolarsComputeEngine._execute_pipeline(...)

    result_queue.put({
        'job_id': job_id,
        'status': JobStatus.COMPLETED,
        'data': result_data,
    })

except Exception as e:
    result_queue.put({
        'job_id': job_id,
        'status': JobStatus.FAILED,
        'error': str(e),
    })
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Column not found` | Invalid column name | Check schema |
| `Pipeline contains a cycle` | Circular dependencies | Remove cycle |
| `Multiple dependencies` | Merge not supported | Use single parent |
| `Unsupported operation` | Unknown step type | Check supported ops |
| `Unsupported file type` | Invalid file format | Use CSV/Parquet/JSON |

## Result Structure

```python
{
    'schema': {
        'name': 'String',
        'age': 'Int64',
        'salary': 'Float64',
        'active': 'Boolean'
    },
    'row_count': 10000,
    'sample_data': [
        {'name': 'Alice', 'age': 30, 'salary': 75000.0, 'active': True},
        {'name': 'Bob', 'age': 25, 'salary': 65000.0, 'active': True},
        # ... up to 5000 rows
    ]
}
```

## Performance Considerations

### Memory Efficiency

- LazyFrame: No data loaded until `.collect()`
- Sample limit: Only 5000 rows returned
- Streaming: Large files processed in chunks

### CPU Efficiency

- Parallel execution: Polars uses all CPU cores
- Query optimization: Operations combined/reordered
- Predicate pushdown: Filter early, read less data

### Best Practices

1. **Filter early**: Place filters before heavy operations
2. **Select early**: Drop unneeded columns ASAP
3. **Avoid collect loops**: Don't collect multiple times
4. **Use appropriate types**: Let Polars infer types

## See Also

- [Architecture](./architecture.md) - Engine architecture
- [Operations](./operations.md) - Supported operations
- [Step Converter](../modules/compute.md#step-converter) - Conversion details
