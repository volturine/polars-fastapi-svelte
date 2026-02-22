# Chart Enrichment Plan — Contour-Inspired Visualization

> **Goal**: Transform our charts from basic visualizations to enterprise-grade, highly customizable data exploration tools comparable to Palantir Contour.

## Current State vs. Contour

| Feature | Our Current | Contour | Gap |
|---------|-------------|---------|-----|
| Chart types | 6 (bar, line, pie, scatter, histogram, boxplot) | 10+ (adds horizontal bar, stacked, area, heatgrid, treemap, gantt) | Missing 4+ types |
| Aggregations | 5 (sum, mean, count, min, max) | 9 (adds unique_count, median, std, variance) | Missing 4 |
| Grouping/segmentation | Basic (scatter only) | Full segmentation on all chart types | Major gap |
| Sorting control | None (fixed by chart type) | X/Y/custom column, asc/desc | Missing entirely |
| Axis formatting | None | Scale type (linear/log), min/max, tick interval, units | Missing entirely |
| Overlays | None | Multiple layers, dual Y-axis | Missing entirely |
| Bucketing | Histogram only (bin count) | Date/time bucketing, auto-bucket, custom intervals | Missing for dates |
| Legend control | Auto-generated | Position (4 options), toggle on/off | Limited |
| Colors | Hardcoded palette | Custom per-series, dashed lines | Limited |
| Interactivity | Tooltips only | Pan/zoom, area selection, click filtering | Missing |
| Labels | Value labels on bars | Position control (start/middle/end/outside) | Limited |

---

## Implementation Tiers

### Tier 1: Configuration Foundation (Est. 2-3 days)
*Add the config options and backend support before touching visuals*

#### 1.1 Extend Config Schema
- [ ] Add to `PlotConfigData` interface:
  ```typescript
  // Sorting
  sort_by: 'x' | 'y' | 'custom' | null
  sort_order: 'asc' | 'desc'
  sort_column: string | null  // for custom sort
  
  // Axis formatting
  x_axis_label: string | null
  y_axis_label: string | null
  y_axis_scale: 'linear' | 'log'
  y_axis_min: number | null
  y_axis_max: number | null
  display_units: '' | 'K' | 'M' | 'B' | '%'
  decimal_places: number  // 0-4
  
  // Legend
  legend_position: 'top' | 'bottom' | 'left' | 'right' | 'none'
  
  // Chart title
  title: string | null
  ```

#### 1.2 Extend Backend Aggregations
- [ ] Add to `plot.py`:
  - `median` → `pl.col(col).median()`
  - `std` → `pl.col(col).std()`
  - `variance` → `pl.col(col).var()`
  - `unique_count` → `pl.col(col).n_unique()`
- [ ] Update `PlotConfigData` Pydantic model with new options
- [ ] Pass sorting config to chart data computation

#### 1.3 Extend PlotConfig.svelte UI
- [ ] Add collapsible "Sort Options" section
- [ ] Add collapsible "Format Options" section
- [ ] Add "Chart Title" input
- [ ] Update visibility logic based on chart type

---

### Tier 2: Chart Type Extensions (Est. 2-3 days)
*Add new chart types to expand visualization options*

#### 2.1 Horizontal Bar Chart
- [ ] Add `'horizontal_bar'` to chart types
- [ ] Backend: Swap x/y in aggregation output
- [ ] Frontend: Render bars horizontally using D3

#### 2.2 Stacked Bar Chart
- [ ] Add `stack_mode: 'grouped' | 'stacked' | '100%'` config option
- [ ] Backend: Compute grouped data, front-end handles stacking
- [ ] Frontend: Implement stacked bar rendering with proper totals

#### 2.3 Area Chart
- [ ] Add `'area'` to chart types (line with fill)
- [ ] Support stacked areas when grouped
- [ ] Add `area_opacity` config option

#### 2.4 Heat Grid (2D Histogram)
- [ ] Add `'heatgrid'` to chart types
- [ ] Add `y_column` for second dimension
- [ ] Backend: Compute 2D aggregation (x_column × y_column)
- [ ] Frontend: Render as colored grid cells with legend

---

### Tier 3: Advanced Segmentation (Est. 2-3 days)
*Enable grouping across all chart types like Contour*

#### 3.1 Universal Group Column
- [ ] Add `group_column` to ALL chart types (not just scatter)
- [ ] Bar: grouped or stacked bars by group_column
- [ ] Line: multiple lines per group
- [ ] Pie: inner ring breakdown or side-by-side pies
- [ ] Scatter: colored by group (already supported)

#### 3.2 Group Sorting
- [ ] Add `group_sort_by: 'name' | 'value' | 'custom'`
- [ ] Add `group_sort_order: 'asc' | 'desc'`
- [ ] Implement drag-to-reorder groups in legend (stretch)

#### 3.3 Series Colors
- [ ] Add `series_colors: string[]` config
- [ ] Allow per-series color picker in UI
- [ ] Default to enterprise palette when not specified

---

### Tier 4: Date/Time Intelligence (Est. 2 days)
*Handle temporal data like Contour's time series board*

#### 4.1 Date Bucketing
- [ ] Detect date/datetime columns automatically
- [ ] Add `date_bucket: 'exact' | 'year' | 'quarter' | 'month' | 'week' | 'day' | 'hour'` config
- [ ] Backend: Apply date truncation before aggregation
- [ ] Frontend: Format axis labels appropriately for time series

#### 4.2 Ordinal Date Bucketing
- [ ] Add `date_ordinal: 'day_of_week' | 'month_of_year' | 'quarter_of_year'`
- [ ] Useful for patterns (e.g., sales by day of week)

#### 4.3 Time Series Chart Type
- [ ] Consider adding explicit `'timeseries'` chart type
- [ ] Auto-detect and suggest when x_column is datetime

---

### Tier 5: Interactivity & Selection (Est. 2-3 days)
*Enable data exploration through chart interaction*

#### 5.1 Pan & Zoom
- [ ] Add `pan_zoom_enabled: boolean` config
- [ ] Implement D3 zoom behavior on scatter/line charts
- [ ] Add reset zoom button
- [ ] Sync zoom state across charts with same data (stretch)

#### 5.2 Click Selection
- [ ] Add `selection_enabled: boolean` config
- [ ] Single-click to highlight bar/point
- [ ] Multi-select with Ctrl/Cmd+click
- [ ] Expose selection through callback/event

#### 5.3 Area Selection (Scatter only)
- [ ] Add `area_selection_enabled: boolean` config
- [ ] Draw rectangle to select points
- [ ] Filter downstream data based on selection

#### 5.4 Interactive Legend
- [ ] Click legend item to toggle series visibility
- [ ] Ctrl/Cmd+click to isolate series
- [ ] Drag to reorder series (affects draw order)

---

### Tier 6: Overlays & Dual Axis (Est. 2-3 days)
*Enable multi-layer visualizations*

#### 6.1 Overlay Support
- [ ] Add `overlays: OverlayConfig[]` to chart config
- [ ] Each overlay has its own chart_type, x_column, y_column, aggregation
- [ ] Render overlays on same chart area

#### 6.2 Dual Y-Axis
- [ ] Add `y_axis_position: 'left' | 'right'` per layer
- [ ] Render secondary Y-axis on right side
- [ ] Sync domain ranges or allow independent scaling

#### 6.3 Reference Lines
- [ ] Add `reference_lines: ReferenceLineConfig[]`
- [ ] Support horizontal (target) and vertical (milestone) lines
- [ ] Configurable color, dash pattern, label

---

### Tier 7: Polish & Export (Est. 1-2 days)
*Final touches for production readiness*

#### 7.1 Export Options
- [ ] Add "Export as PNG" button
- [ ] Add "Export data as CSV" button
- [ ] Consider "Copy to clipboard" for chart image

#### 7.2 Responsive Behavior
- [ ] Implement proper resize handling (already partially done)
- [ ] Adjust label density based on chart width
- [ ] Mobile-friendly legend collapsing

#### 7.3 Accessibility
- [ ] Add ARIA labels to chart elements
- [ ] Keyboard navigation for interactive elements
- [ ] High contrast mode support

---

## Technical Architecture

### Config Schema Evolution

```typescript
// operation-config.ts - Extended PlotConfigData
interface PlotConfigData {
  // Existing
  chart_type: ChartType;
  x_column: string;
  y_column: string | null;
  bins: number;
  aggregation: AggregationType;
  group_column: string | null;
  
  // Tier 1: Configuration Foundation
  sort_by: 'x' | 'y' | 'custom' | null;
  sort_order: 'asc' | 'desc';
  sort_column: string | null;
  x_axis_label: string | null;
  y_axis_label: string | null;
  y_axis_scale: 'linear' | 'log';
  y_axis_min: number | null;
  y_axis_max: number | null;
  display_units: '' | 'K' | 'M' | 'B' | '%';
  decimal_places: number;
  legend_position: 'top' | 'bottom' | 'left' | 'right' | 'none';
  title: string | null;
  
  // Tier 2: Chart Type Extensions
  stack_mode: 'grouped' | 'stacked' | '100%';
  area_opacity: number; // 0-1
  
  // Tier 3: Advanced Segmentation
  group_sort_by: 'name' | 'value' | 'custom';
  group_sort_order: 'asc' | 'desc';
  series_colors: string[];
  
  // Tier 4: Date/Time Intelligence
  date_bucket: DateBucketType | null;
  date_ordinal: DateOrdinalType | null;
  
  // Tier 5: Interactivity
  pan_zoom_enabled: boolean;
  selection_enabled: boolean;
  area_selection_enabled: boolean;
  
  // Tier 6: Overlays
  overlays: OverlayConfig[];
  reference_lines: ReferenceLineConfig[];
}

type ChartType = 
  | 'bar' | 'horizontal_bar' | 'line' | 'area' | 'pie' 
  | 'scatter' | 'histogram' | 'boxplot' | 'heatgrid' | 'treemap';

type AggregationType = 
  | 'sum' | 'mean' | 'count' | 'min' | 'max' 
  | 'median' | 'std' | 'variance' | 'unique_count';

type DateBucketType = 'exact' | 'year' | 'quarter' | 'month' | 'week' | 'day' | 'hour';
type DateOrdinalType = 'day_of_week' | 'month_of_year' | 'quarter_of_year';

interface OverlayConfig {
  chart_type: 'bar' | 'line' | 'scatter';
  x_column: string;
  y_column: string;
  aggregation: AggregationType;
  y_axis_position: 'left' | 'right';
  color: string | null;
  dashed: boolean;
}

interface ReferenceLineConfig {
  axis: 'x' | 'y';
  value: number;
  label: string | null;
  color: string;
  dashed: boolean;
}
```

### Backend Changes (plot.py)

```python
# Extended aggregation mapping
AGGREGATIONS = {
    'sum': lambda col: pl.col(col).sum(),
    'mean': lambda col: pl.col(col).mean(),
    'count': lambda col: pl.col(col).count(),
    'min': lambda col: pl.col(col).min(),
    'max': lambda col: pl.col(col).max(),
    'median': lambda col: pl.col(col).median(),
    'std': lambda col: pl.col(col).std(),
    'variance': lambda col: pl.col(col).var(),
    'unique_count': lambda col: pl.col(col).n_unique(),
}

# Date bucketing functions
def apply_date_bucket(df: pl.DataFrame, column: str, bucket: str) -> pl.DataFrame:
    if bucket == 'exact':
        return df
    elif bucket in ('year', 'month', 'week', 'day', 'hour'):
        return df.with_columns(pl.col(column).dt.truncate(bucket).alias(column))
    # ... ordinal handling
```

### Frontend Changes (ChartPreview.svelte)

Key modifications needed:
1. Accept extended config prop
2. Apply sorting before rendering
3. Configure D3 axes based on scale/min/max/units
4. Handle new chart types (horizontal_bar, area, heatgrid)
5. Implement stacking logic
6. Add zoom/pan behaviors
7. Render overlays and reference lines

---

## Priority Recommendation

**Start with Tier 1** (Configuration Foundation) as it enables all other work. Then proceed to:

1. **Tier 3** (Advanced Segmentation) — biggest impact on usefulness
2. **Tier 2** (Chart Types) — more visualization options
3. **Tier 5** (Interactivity) — enables data exploration
4. **Tier 4** (Date/Time) — essential for time series
5. **Tier 6** (Overlays) — advanced feature
6. **Tier 7** (Polish) — finishing touches

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Chart types | 6 | 10+ |
| Configuration options | 6 | 25+ |
| Aggregation types | 5 | 9 |
| Interactive features | 1 (tooltip) | 5+ |
| Time to configure basic chart | ~30s | ~15s |
| Data exploration workflows supported | 1 | 5+ |
