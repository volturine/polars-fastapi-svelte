# Building Pipelines

Complete guide to building data transformation pipelines.

## Overview

The visual pipeline builder lets you create data transformations by connecting operations. Each step transforms data from the previous step, forming a Directed Acyclic Graph (DAG).

## Pipeline Editor Interface

```
┌──────────────────────────────────────────────────────────────────────┐
│  [Save] [Run] [Export]                              Analysis Name ▼   │
├──────────────┬─────────────────────────────┬─────────────────────────┤
│              │                             │                         │
│   Step       │        Pipeline             │      Configuration      │
│   Library    │        Canvas               │      Panel              │
│              │                             │                         │
│   ┌───────┐  │     ┌─────────┐            │   ┌─────────────────┐   │
│   │Filter │  │     │DataSource│            │   │ Filter Config   │   │
│   ├───────┤  │     └────┬────┘            │   │                 │   │
│   │Select │  │          │                 │   │ Column: [▼]     │   │
│   ├───────┤  │          ▼                 │   │ Operator: [▼]   │   │
│   │Sort   │  │     ┌─────────┐            │   │ Value: [____]   │   │
│   ├───────┤  │     │ Filter  │◄──selected │   │                 │   │
│   │GroupBy│  │     └────┬────┘            │   │ [Add Condition] │   │
│   └───────┘  │          │                 │   │                 │   │
│              │          ▼                 │   │ Logic: AND ○ OR │   │
│              │     ┌─────────┐            │   └─────────────────┘   │
│              │     │ Select  │            │                         │
│              │     └─────────┘            │                         │
│              │                             │                         │
└──────────────┴─────────────────────────────┴─────────────────────────┘
```

## Adding Operations

### Method 1: Drag and Drop

1. Find the operation in the **Step Library**
2. Drag it onto the **Canvas**
3. Drop it on a connection line or after a step

### Method 2: Context Menu

1. Right-click on a step
2. Select **"Add Step After"**
3. Choose the operation type

## Configuring Steps

1. **Click** a step to select it
2. The **Configuration Panel** shows settings
3. Fill in the required fields
4. Changes auto-save (with debounce)

## Step Types

### Filtering Operations

**Filter** - Remove rows based on conditions
```
Column: age
Operator: >
Value: 18
Logic: AND
```

**Limit** - Keep first N rows
```
N: 100
```

**Sample** - Random sample
```
Method: Count (N: 1000) or Fraction (10%)
Shuffle: Yes/No
Seed: 42 (optional)
```

**TopK** - Top rows by column
```
Column: sales
K: 10
Descending: Yes
```

### Selection Operations

**Select** - Keep specific columns
```
Columns: [name, age, city]
```

**Drop** - Remove columns
```
Columns: [temp_col, debug_col]
```

**Rename** - Rename columns
```
Mappings:
  old_name → new_name
  another → renamed
```

### Aggregation Operations

**GroupBy** - Group and aggregate
```
Group By: [category, region]
Aggregations:
  - sales → sum
  - quantity → mean
  - id → count
```

**Value Counts** - Frequency count
```
Column: category
Normalize: No
Sort: Yes
```

### Transformation Operations

**Sort** - Order rows
```
Columns: [date, name]
Descending: [Yes, No]
```

**Deduplicate** - Remove duplicates
```
Subset: [email] (or all columns)
Keep: First / Last / None
```

**Fill Null** - Handle missing values
```
Strategy: Literal / Forward / Backward / Mean / Median / Drop
Value: 0 (for Literal)
Columns: [price, quantity]
```

### Reshaping Operations

**Pivot** - Wide format
```
Index: [date]
Columns: category
Values: sales
Aggregate: sum
```

**Unpivot** - Long format
```
Index: [id, name]
On: [jan, feb, mar]
Variable Name: month
Value Name: value
```

**Explode** - Expand lists
```
Columns: [tags]
```

### String Operations

**String Transform**
```
Column: name
Method: uppercase / lowercase / trim / replace
New Column: name_clean (optional)
```

### Time Series Operations

**Timeseries**
```
Column: created_at
Operation: extract / add / subtract / diff
Component: year / month / day / hour
New Column: year
```

## Understanding Dependencies

### Linear Pipeline

```
DataSource → Filter → Select → Sort → Result
```

Each step depends on the previous one.

### Branching (Future)

```
                    ┌→ Aggregate A
DataSource → Filter ┤
                    └→ Aggregate B
```

Multiple steps can depend on the same parent.

## Schema Preview

As you build, the **Schema Viewer** shows:
- Current columns
- Data types
- Row count estimate

This is calculated client-side without executing.

## Executing Pipelines

### Run Pipeline

1. Click **Run** in the toolbar
2. Watch progress indicator
3. View results when complete

### Execution Flow

```
Click Run
    │
    ▼
Frontend sends to /compute/execute
    │
    ▼
Backend spawns compute engine
    │
    ▼
Engine loads data (lazy)
    │
    ▼
Engine applies transformations
    │
    ▼
Results returned (sample + stats)
    │
    ▼
Frontend displays preview
```

### Viewing Results

After execution:
- **Data Table**: First 5000 rows
- **Schema**: Column types
- **Stats**: Row count, execution info

## Exporting Results

### Export Formats

| Format | Best For |
|--------|----------|
| CSV | Spreadsheets, general use |
| Parquet | Large data, preserves types |
| JSON | APIs, web applications |

### Export Process

1. Click **Export**
2. Choose format
3. File downloads automatically

## Best Practices

### 1. Filter Early

Place filters at the beginning to reduce data volume:

```
Good:  DataSource → Filter → GroupBy → Sort
Bad:   DataSource → GroupBy → Filter → Sort
```

### 2. Select What You Need

Drop unnecessary columns early:

```
Good:  DataSource → Select [needed cols] → Transform
Bad:   DataSource → Transform → Select [needed cols]
```

### 3. Preview Before Executing

Use the schema preview to verify transformations before running.

### 4. Name Steps Clearly

Rename steps for clarity in complex pipelines.

### 5. Save Frequently

Changes auto-save, but click Save for important checkpoints.

## Troubleshooting

### Step shows error

- Check configuration panel for validation errors
- Ensure column names exist in input schema
- Verify data types match operation requirements

### Pipeline won't execute

- Ensure datasource is accessible
- Check for cyclic dependencies
- Verify all steps are configured

### Results look wrong

- Review each step's configuration
- Check filter conditions
- Verify aggregation functions

## See Also

- [Creating Datasources](./creating-datasources.md) - Data source setup
- [Operations Reference](../reference/polars-operations.md) - All operations
- [Compute Engine](../backend/compute-engine/README.md) - Execution details
