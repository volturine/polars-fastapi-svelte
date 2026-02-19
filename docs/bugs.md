# Bugs and Issues and feature requests

## Lazyframe cross-tab build/preview execution

We need to redesign analysis execution so **lazyframe inputs are executed inside the same engine run** and not reconstructed from datasource fetches.

### Desired execution model

Example analysis tabs (single analysis ID):

```
tab1: datasource 1 -> transform logic -> export 1
tab2: lazyframe input (tab1) -> transform logic -> export 2
tab3: lazyframe input (tab2) -> transform logic -> export 3
```

Build targets must execute only the required upstream chain **within the same engine execution**, forwarding LazyFrames between tabs:

1. **Targeting export 1** should build:
   - load datasource 1
   - tab1 transform logic
   - export 1

2. **Targeting export 2** should build:
   - load datasource 1
   - tab1 transform logic
   - export 1 (but still forward the LazyFrame from tab1 downstream)
   - tab2 transform logic
   - export 2

3. **Targeting export 3** should build:
   - load datasource 1
   - tab1 transform logic
   - export 1 (LazyFrame forwarded)
   - tab2 transform logic
   - export 2 (LazyFrame forwarded)
   - tab3 transform logic
   - export 3

### Requirements
- Preceding tabs must execute in dependency order in the **same engine**.
- Lazyframe outputs are forwarded downstream; no reloading from output datasources.
- Previews & chart visualizations should reuse the same engine for the analysis and should forward LazyFrames within that engine.
- The full analysis pipeline is sent on preview/build so the engine can execute the full chain deterministically.

## Analysis experience inconsistencies + unified DAG requirement (clarification)

### Current issues
- New analysis creation is not prepopulated with an inline DataTable/view step, while new tab creation is.
- Datasource selection for new tab allows choosing an analysis tab, but the datasource node does not support it yet.
- Cross-tab work requires additional compute that should be unnecessary.
- Derived analysis tabs created before saving do not have LazyFrame schema; they only work after save.

### Required behavior
- Treat the analysis as **one big DAG** (backend + frontend): tabs are **frontend-only visualization** and grouping, not execution boundaries.
- Backend should treat analysis as a single transform file, resolving everything in one request using the full pipeline payload.
- Input datasource should be resolved immediately (LazyFrame) when the analysis is in the same DAG; no intermediate datasource reloads.
- Cross-tab previews/exports should reuse the same engine run and forward LazyFrames within that run.
