# TypeScript Type Definitions

Complete reference for TypeScript types used in the frontend.

## Core Types

### Analysis Types

Located in `frontend/src/lib/types/analysis.ts`:

#### PipelineStep

Represents a single step in a transformation pipeline.

```typescript
interface PipelineStep {
    id: string;              // Unique step identifier
    type: string;            // Operation type (e.g., 'filter', 'select')
    config: Record<string, unknown>;  // Step configuration
    depends_on: string[];    // IDs of parent steps
}
```

#### AnalysisTab

Represents a tab in the analysis editor.

```typescript
type AnalysisTabType = 'datasource' | 'derived';

interface AnalysisTab {
    id: string;                    // Unique tab identifier
    name: string;                  // Display name
    type: AnalysisTabType;         // Tab type
    parent_id: string | null;      // Parent tab (for derived)
    datasource_id: string | null;  // Source datasource
    steps: PipelineStep[];         // Pipeline steps
}
```

#### Analysis

Complete analysis object.

```typescript
interface Analysis {
    id: string;
    name: string;
    description: string | null;
    pipeline_definition: Record<string, unknown>;
    status: string;
    created_at: string;
    updated_at: string;
    result_path: string | null;
    thumbnail: string | null;
    tabs: AnalysisTab[];
}
```

#### AnalysisCreate

Payload for creating a new analysis.

```typescript
interface AnalysisCreate {
    name: string;
    description?: string | null;
    datasource_ids: string[];
    pipeline_steps: PipelineStep[];
    tabs: AnalysisTab[];
}
```

#### AnalysisUpdate

Payload for updating an analysis.

```typescript
interface AnalysisUpdate {
    name?: string | null;
    description?: string | null;
    pipeline_steps?: PipelineStep[] | null;
    status?: string | null;
    tabs?: AnalysisTab[] | null;
}
```

#### AnalysisGalleryItem

Summary for gallery view.

```typescript
interface AnalysisGalleryItem {
    id: string;
    name: string;
    thumbnail: string | null;
    created_at: string;
    updated_at: string;
    row_count: number | null;
    column_count: number | null;
}
```

## DataSource Types

Located in `frontend/src/lib/types/datasource.ts`:

#### ColumnSchema

Schema information for a single column.

```typescript
interface ColumnSchema {
    name: string;      // Column name
    dtype: string;     // Polars data type
    nullable: boolean; // Can contain nulls
}
```

#### SchemaInfo

Complete schema information.

```typescript
interface SchemaInfo {
    columns: ColumnSchema[];
    row_count: number | null;
}
```

#### DataSource

Complete datasource object.

```typescript
interface DataSource {
    id: string;
    name: string;
    source_type: string;
    config: Record<string, unknown>;
    schema_cache: Record<string, unknown> | null;
    created_at: string;
}
```

#### DataSourceCreate

Payload for creating a datasource.

```typescript
interface DataSourceCreate {
    name: string;
    source_type: string;
    config: Record<string, unknown>;
}
```

#### Config Types

```typescript
interface FileDataSourceConfig {
    file_path: string;
    file_type: string;
    options?: Record<string, unknown>;
}

interface DatabaseDataSourceConfig {
    connection_string: string;
    query: string;
}

interface APIDataSourceConfig {
    url: string;
    method?: string;
    headers?: Record<string, string> | null;
    auth?: Record<string, unknown> | null;
}
```

## Compute Types

Located in `frontend/src/lib/types/compute.ts`:

#### ComputeStatus

Status of a compute job.

```typescript
type ComputeStatus = 'pending' | 'running' | 'completed' | 'failed';
```

#### EngineStatus

Status of a compute engine process.

```typescript
type EngineStatus = 'idle' | 'running' | 'error' | 'terminated';
```

#### ComputeJob

Compute job information.

```typescript
interface ComputeJob {
    id: string;
    status: ComputeStatus;
    progress?: number;
    error?: string | null;
    result?: unknown;
    current_step?: string | null;
    created_at?: string;
    updated_at?: string;
}
```

#### EngineStatusResponse

Engine status response from API.

```typescript
interface EngineStatusResponse {
    analysis_id: string;
    status: EngineStatus;
    process_id: number | null;
    last_activity: string | null;
}
```

## Operation Config Types

Located in `frontend/src/lib/types/operation-config.ts`:

#### FilterConfigData

```typescript
interface FilterCondition {
    column: string;
    operator: string;
    value: string;
}

interface FilterConfigData {
    conditions: FilterCondition[];
    logic: 'AND' | 'OR';
}
```

#### SelectConfigData

```typescript
interface SelectConfigData {
    columns: string[];
}
```

#### GroupByConfigData

```typescript
interface Aggregation {
    column: string;
    function: string;
    alias: string;
}

interface GroupByConfigData {
    groupBy: string[];
    aggregations: Aggregation[];
}
```

#### SortConfigData

```typescript
interface SortRule {
    column: string;
    descending: boolean;
}

type SortConfigData = SortRule[];
```

#### RenameConfigData

```typescript
interface RenameConfigData {
    column_mapping: Record<string, string>;
}
```

#### DropConfigData

```typescript
interface DropConfigData {
    columns: string[];
}
```

#### JoinConfigData

```typescript
interface JoinConfigData {
    how: 'inner' | 'left' | 'right' | 'outer';
    left_on: string[];
    right_on: string[];
}
```

#### DeduplicateConfigData

```typescript
interface DeduplicateConfigData {
    subset: string[] | null;
    keep: string;
}
```

#### FillNullConfigData

```typescript
interface FillNullConfigData {
    strategy: string;
    columns: string[] | null;
    value?: string | number;
}
```

#### ExplodeConfigData

```typescript
interface ExplodeConfigData {
    columns: string[];
}
```

#### PivotConfigData

```typescript
interface PivotConfigData {
    index: string[];
    columns: string;
    values: string;
    aggregate_function: string;
}
```

#### UnpivotConfigData

```typescript
interface UnpivotConfigData {
    index?: string[];
    on?: string[];
    variable_name?: string;
    value_name?: string;
}
```

#### TimeSeriesConfigData

```typescript
interface TimeSeriesConfigData {
    column: string;
    operation_type: string;
    new_column: string;
    component?: string;
    value?: number;
    unit?: string;
    column2?: string;
}
```

#### StringMethodsConfigData

```typescript
interface StringMethodsConfigData {
    column: string;
    method: string;
    new_column: string;
    start?: number;
    end?: number | null;
    pattern?: string;
    replacement?: string;
    group_index?: number;
    delimiter?: string;
    index?: number;
}
```

#### ViewConfigData

```typescript
interface ViewConfigData {
    rowLimit: number;
}
```

#### SampleConfigData

```typescript
interface SampleConfigData {
    n?: number;
    fraction?: number;
    shuffle?: boolean;
    seed?: number;
}
```

#### LimitConfigData

```typescript
interface LimitConfigData {
    n: number;
}
```

#### TopKConfigData

```typescript
interface TopKConfigData {
    column: string;
    k: number;
    descending: boolean;
}
```

#### ValueCountsConfigData

```typescript
interface ValueCountsConfigData {
    column: string;
    normalize?: boolean;
    sort?: boolean;
}
```

#### NullCountConfigData

```typescript
interface NullCountConfigData extends Record<string, never> {}
```

#### OperationConfig Union

```typescript
type OperationConfig =
    | FilterConfigData
    | SelectConfigData
    | GroupByConfigData
    | SortConfigData
    | RenameConfigData
    | DropConfigData
    | JoinConfigData
    | ExpressionConfigData
    | DeduplicateConfigData
    | FillNullConfigData
    | ExplodeConfigData
    | PivotConfigData
    | TimeSeriesConfigData
    | StringMethodsConfigData
    | ViewConfigData
    | SampleConfigData
    | LimitConfigData
    | TopKConfigData
    | NullCountConfigData
    | ValueCountsConfigData
    | UnpivotConfigData;
```

## API Response Types

Located in `frontend/src/lib/types/api-responses.ts`:

#### Generic Types

```typescript
interface ApiError {
    type: 'network' | 'http' | 'parse' | 'unknown';
    message: string;
    status?: number;
}

type ApiResponse<T> = {
    data: T;
    error: null;
} | {
    data: null;
    error: ApiError;
};
```

## Schema Utility Types

Located in `frontend/src/lib/types/schema.ts`:

#### Polars Data Types

```typescript
type PolarsNumericType =
    | 'Int8' | 'Int16' | 'Int32' | 'Int64'
    | 'UInt8' | 'UInt16' | 'UInt32' | 'UInt64'
    | 'Float32' | 'Float64';

type PolarsStringType = 'String' | 'Utf8';

type PolarsBooleanType = 'Boolean';

type PolarsTemporalType = 'Date' | 'Datetime' | 'Duration' | 'Time';

type PolarsComplexType = 'List' | 'Struct' | 'Object';

type PolarsDataType =
    | PolarsNumericType
    | PolarsStringType
    | PolarsBooleanType
    | PolarsTemporalType
    | PolarsComplexType
    | 'Null';
```

## Type Guards

Useful type guard functions:

```typescript
// Check if value is a valid operation config
function isFilterConfig(config: OperationConfig): config is FilterConfigData {
    return 'conditions' in config && 'logic' in config;
}

function isSelectConfig(config: OperationConfig): config is SelectConfigData {
    return 'columns' in config && !('groupBy' in config);
}

function isGroupByConfig(config: OperationConfig): config is GroupByConfigData {
    return 'groupBy' in config && 'aggregations' in config;
}
```

## Usage Examples

### Creating a Pipeline Step

```typescript
import type { PipelineStep, FilterConfigData } from '$lib/types';

const filterConfig: FilterConfigData = {
    conditions: [
        { column: 'age', operator: '>=', value: '18' }
    ],
    logic: 'AND'
};

const step: PipelineStep = {
    id: crypto.randomUUID(),
    type: 'filter',
    config: filterConfig,
    depends_on: []
};
```

### Working with Analysis

```typescript
import type { Analysis, AnalysisUpdate } from '$lib/types';

function updateAnalysisName(analysis: Analysis, newName: string): AnalysisUpdate {
    return {
        name: newName
    };
}
```

### Handling API Responses

```typescript
import type { ComputeJob, ComputeStatus } from '$lib/types';

function isJobComplete(job: ComputeJob): boolean {
    return job.status === 'completed' || job.status === 'failed';
}

function getJobProgress(job: ComputeJob): number {
    return job.progress ?? 0;
}
```

## See Also

- [API Client](../frontend/api-client/README.md) - API client implementation
- [State Management](../frontend/state-management/README.md) - Store implementations
- [Polars Operations](./polars-operations.md) - Operation reference
