import logging
from typing import Any

import polars as pl

logger = logging.getLogger(__name__)


def _cast_value(value: Any, value_type: str | None) -> Any:
    """Cast a value to the specified type for Polars operations."""
    if value_type == 'Int64':
        return int(value) if value is not None else value
    if value_type == 'Float64':
        return float(value) if value is not None else value
    if value_type == 'Boolean':
        if isinstance(value, str):
            return value.strip().lower() in {'true', '1', 'yes'}
        return bool(value)
    if value_type == 'Date':
        return pl.lit(value).cast(pl.Date)
    if value_type == 'Datetime':
        return pl.lit(value).cast(pl.Datetime)
    return value


def _handle_filter(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle filter operation."""
    conditions = params.get('conditions', [])
    logic = params.get('logic', 'AND')

    if not conditions:
        raise ValueError('Filter requires at least one condition')

    # Build expression for each condition
    exprs = []
    for cond in conditions:
        column = cond['column']
        operator = cond.get('operator', '==')
        value = cond['value']

        col = pl.col(column)

        # Build appropriate Polars expression based on operator
        if operator == '=' or operator == '==':
            expr = col == value
        elif operator == '!=':
            expr = col != value
        elif operator == '>':
            expr = col > value
        elif operator == '<':
            expr = col < value
        elif operator == '>=':
            expr = col >= value
        elif operator == '<=':
            expr = col <= value
        elif operator == 'contains':
            expr = col.str.contains(value)
        elif operator == 'starts_with':
            expr = col.str.starts_with(value)
        elif operator == 'ends_with':
            expr = col.str.ends_with(value)
        else:
            raise ValueError(f'Unsupported filter operator: {operator}')

        exprs.append(expr)

    # Combine expressions with AND or OR logic
    if len(exprs) == 1:
        final_expr = exprs[0]
    elif logic == 'AND':
        final_expr = exprs[0]
        for expr in exprs[1:]:
            final_expr = final_expr & expr
    elif logic == 'OR':
        final_expr = exprs[0]
        for expr in exprs[1:]:
            final_expr = final_expr | expr
    else:
        raise ValueError(f'Unsupported logic operator: {logic}')

    return lf.filter(final_expr)


def _handle_select(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle select operation."""
    columns = params.get('columns', [])
    return lf.select(columns)


def _handle_groupby(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle groupby operation."""
    group_cols = params.get('group_by', [])
    agg_cols = params.get('aggregations', [])

    agg_exprs = []
    for agg in agg_cols:
        col = agg['column']
        func = agg['function']
        alias = agg.get('alias')

        if func == 'sum':
            agg_exprs.append(pl.col(col).sum().alias(alias or f'{col}_sum'))
        elif func == 'mean':
            agg_exprs.append(pl.col(col).mean().alias(alias or f'{col}_mean'))
        elif func == 'count':
            agg_exprs.append(pl.col(col).count().alias(alias or f'{col}_count'))
        elif func == 'min':
            agg_exprs.append(pl.col(col).min().alias(alias or f'{col}_min'))
        elif func == 'max':
            agg_exprs.append(pl.col(col).max().alias(alias or f'{col}_max'))
        elif func == 'first':
            agg_exprs.append(pl.col(col).first().alias(alias or f'{col}_first'))
        elif func == 'last':
            agg_exprs.append(pl.col(col).last().alias(alias or f'{col}_last'))
        elif func == 'median':
            agg_exprs.append(pl.col(col).median().alias(alias or f'{col}_median'))
        elif func == 'std':
            agg_exprs.append(pl.col(col).std().alias(alias or f'{col}_std'))
        elif func == 'collect_list':
            agg_exprs.append(pl.col(col).implode().alias(alias or f'{col}_list'))
        elif func == 'collect_set':
            agg_exprs.append(pl.col(col).implode().list.unique().alias(alias or f'{col}_set'))

    return lf.group_by(group_cols).agg(agg_exprs)


def _handle_sort(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle sort operation."""
    columns = params.get('columns', [])
    descending = params.get('descending', False)
    # Handle both single boolean and list of booleans for descending
    if isinstance(descending, list) and len(descending) != len(columns):
        # Ensure descending list matches columns length
        descending = descending[: len(columns)] if len(descending) > len(columns) else descending + [False] * (len(columns) - len(descending))
    return lf.sort(columns, descending=descending)


def _handle_rename(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle rename operation."""
    mapping = params.get('mapping', {})
    return lf.rename(mapping)


def _handle_with_columns(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle with_columns operation."""
    expressions = params.get('expressions', [])
    new_cols = []

    for expr in expressions:
        col_name = expr['name']
        expr_type = expr['type']

        if expr_type == 'literal':
            new_cols.append(pl.lit(expr['value']).alias(col_name))
        elif expr_type == 'column':
            new_cols.append(pl.col(expr['column']).alias(col_name))

    return lf.with_columns(new_cols)


def _handle_drop(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle drop operation."""
    columns = params.get('columns', [])
    return lf.drop(columns)


def _handle_pivot(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle pivot operation."""
    index = params.get('index', [])
    on_column = params.get('columns')
    values = params.get('values')
    aggregate_function = params.get('aggregate_function', 'first')

    if not on_column:
        raise ValueError('Pivot requires a pivot column')

    if not index:
        raise ValueError('Pivot requires at least one index column')
    # .collect_schema().names()

    on_columns = params.get('on_columns') or params.get('onColumns')
    if not on_columns:
        raise ValueError('Pivot requires on_columns to remain lazy; collecting for preview-only is not supported')

    if values:
        return lf.pivot(on=on_column, on_columns=on_columns, index=index, values=values, aggregate_function=aggregate_function)
    return lf.pivot(on=on_column, on_columns=on_columns, index=index, aggregate_function=aggregate_function)


def _handle_timeseries(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle timeseries operation."""
    column = params.get('column')
    operation_type = params.get('operation_type')
    new_column = params.get('new_column')

    if not isinstance(column, str) or not column:
        raise ValueError('timeseries operation requires column parameter')

    if not isinstance(new_column, str) or not new_column:
        raise ValueError('timeseries operation requires new_column parameter')

    if operation_type == 'extract':
        component = params.get('component')
        if component == 'year':
            return lf.with_columns(pl.col(column).dt.year().alias(new_column))
        elif component == 'month':
            return lf.with_columns(pl.col(column).dt.month().alias(new_column))
        elif component == 'day':
            return lf.with_columns(pl.col(column).dt.day().alias(new_column))
        elif component == 'hour':
            return lf.with_columns(pl.col(column).dt.hour().alias(new_column))
        elif component == 'minute':
            return lf.with_columns(pl.col(column).dt.minute().alias(new_column))
        elif component == 'second':
            return lf.with_columns(pl.col(column).dt.second().alias(new_column))
        elif component == 'quarter':
            return lf.with_columns(pl.col(column).dt.quarter().alias(new_column))
        elif component == 'week':
            return lf.with_columns(pl.col(column).dt.week().alias(new_column))
        elif component == 'dayofweek':
            return lf.with_columns(pl.col(column).dt.weekday().alias(new_column))
        else:
            raise ValueError(f'Unsupported time component: {component}')

    elif operation_type == 'add':
        value = params.get('value')
        unit = params.get('unit', 'days')

        if unit not in {'seconds', 'minutes', 'hours', 'days', 'weeks', 'months'}:
            raise ValueError('timeseries operation requires unit parameter')

        if not isinstance(value, (int, float)):
            raise ValueError('timeseries operation requires numeric value parameter')

        if unit == 'months':
            return lf.with_columns(pl.col(column).dt.offset_by(f'{value}mo').alias(new_column))

        if unit == 'seconds':
            duration = pl.duration(seconds=int(value))
            return lf.with_columns((pl.col(column) + duration).alias(new_column))

        if unit == 'minutes':
            duration = pl.duration(minutes=int(value))
            return lf.with_columns((pl.col(column) + duration).alias(new_column))

        if unit == 'hours':
            duration = pl.duration(hours=int(value))
            return lf.with_columns((pl.col(column) + duration).alias(new_column))

        if unit == 'days':
            duration = pl.duration(days=int(value))
            return lf.with_columns((pl.col(column) + duration).alias(new_column))

        duration = pl.duration(weeks=int(value))
        return lf.with_columns((pl.col(column) + duration).alias(new_column))

    elif operation_type == 'subtract':
        value = params.get('value')
        unit = params.get('unit', 'days')

        if unit not in {'seconds', 'minutes', 'hours', 'days', 'weeks', 'months'}:
            raise ValueError('timeseries operation requires unit parameter')

        if not isinstance(value, (int, float)):
            raise ValueError('timeseries operation requires numeric value parameter')

        if unit == 'months':
            return lf.with_columns(pl.col(column).dt.offset_by(f'-{value}mo').alias(new_column))

        if unit == 'seconds':
            duration = pl.duration(seconds=int(value))
            return lf.with_columns((pl.col(column) - duration).alias(new_column))

        if unit == 'minutes':
            duration = pl.duration(minutes=int(value))
            return lf.with_columns((pl.col(column) - duration).alias(new_column))

        if unit == 'hours':
            duration = pl.duration(hours=int(value))
            return lf.with_columns((pl.col(column) - duration).alias(new_column))

        if unit == 'days':
            duration = pl.duration(days=int(value))
            return lf.with_columns((pl.col(column) - duration).alias(new_column))

        duration = pl.duration(weeks=int(value))
        return lf.with_columns((pl.col(column) - duration).alias(new_column))

    elif operation_type == 'diff':
        column2 = params.get('column2')
        if not isinstance(column2, str) or not column2:
            raise ValueError('timeseries operation requires column2 parameter')
        return lf.with_columns((pl.col(column2) - pl.col(column)).alias(new_column))

    else:
        raise ValueError(f'Unsupported timeseries operation: {operation_type}')


def _handle_string_transform(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle string_transform operation."""
    column = params.get('column')
    method = params.get('method')
    new_column = params.get('new_column', column)

    if not isinstance(column, str) or not column:
        raise ValueError('string_transform requires column parameter')

    if not isinstance(new_column, str) or not new_column:
        raise ValueError('string_transform requires new_column parameter')

    if method == 'uppercase':
        return lf.with_columns(pl.col(column).str.to_uppercase().alias(new_column))
    elif method == 'lowercase':
        return lf.with_columns(pl.col(column).str.to_lowercase().alias(new_column))
    elif method == 'title':
        return lf.with_columns(pl.col(column).str.to_titlecase().alias(new_column))
    elif method == 'strip':
        return lf.with_columns(pl.col(column).str.strip_chars().alias(new_column))
    elif method == 'lstrip':
        return lf.with_columns(pl.col(column).str.strip_chars_start().alias(new_column))
    elif method == 'rstrip':
        return lf.with_columns(pl.col(column).str.strip_chars_end().alias(new_column))
    elif method == 'length':
        return lf.with_columns(pl.col(column).str.len_chars().alias(new_column))
    elif method == 'slice':
        start = params.get('start', 0)
        end = params.get('end')
        return lf.with_columns(pl.col(column).str.slice(start, end).alias(new_column))
    elif method == 'replace':
        pattern = params.get('pattern')
        replacement = params.get('replacement', '')
        if not isinstance(pattern, str) or not pattern:
            raise ValueError('string_transform replace requires pattern parameter')
        return lf.with_columns(pl.col(column).str.replace_all(pattern, replacement).alias(new_column))
    elif method == 'extract':
        pattern = params.get('pattern')
        group_index = params.get('group_index', 0)
        if not isinstance(pattern, str) or not pattern:
            raise ValueError('string_transform extract requires pattern parameter')
        return lf.with_columns(pl.col(column).str.extract(pattern, group_index).alias(new_column))
    elif method == 'split':
        delimiter = params.get('delimiter', ' ')
        index = params.get('index', 0)
        if not isinstance(delimiter, str):
            raise ValueError('string_transform split requires delimiter parameter')
        return lf.with_columns(pl.col(column).str.split(delimiter).list.get(index).alias(new_column))
    else:
        raise ValueError(f'Unsupported string method: {method}')


def _handle_fill_null(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle fill_null operation."""
    strategy = params.get('strategy')
    columns = params.get('columns')

    if strategy == 'literal':
        value = params.get('value')
        value_type = params.get('value_type')
        casted = _cast_value(value, value_type)

        def cast_column(col: str) -> pl.Expr:
            expr = pl.col(col)
            if value_type == 'Int64':
                return expr.cast(pl.Int64).fill_null(casted)
            if value_type == 'Float64':
                return expr.cast(pl.Float64).fill_null(casted)
            if value_type == 'Boolean':
                return expr.cast(pl.Boolean).fill_null(casted)
            if value_type == 'Date':
                return expr.cast(pl.Date).fill_null(casted)
            if value_type == 'Datetime':
                return expr.cast(pl.Datetime).fill_null(casted)
            return expr.fill_null(casted)

        if columns:
            return lf.with_columns([cast_column(c) for c in columns])
        return lf.with_columns([cast_column(c) for c in lf.columns])

    elif strategy == 'forward':
        if columns:
            return lf.with_columns([pl.col(c).forward_fill() for c in columns])
        return lf.select([pl.all().forward_fill()])

    elif strategy == 'backward':
        if columns:
            return lf.with_columns([pl.col(c).backward_fill() for c in columns])
        return lf.select([pl.all().backward_fill()])

    elif strategy == 'mean':
        if not columns:
            raise ValueError('Columns must be specified for mean strategy')
        exprs = [pl.col(c).fill_null(pl.col(c).mean()) for c in columns]
        return lf.with_columns(exprs)

    elif strategy == 'median':
        if not columns:
            raise ValueError('Columns must be specified for median strategy')
        exprs = [pl.col(c).fill_null(pl.col(c).median()) for c in columns]
        return lf.with_columns(exprs)

    elif strategy == 'drop_rows':
        if columns:
            return lf.drop_nulls(subset=columns)
        return lf.drop_nulls()

    else:
        raise ValueError(f'Unsupported fill_null strategy: {strategy}')


def _handle_deduplicate(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle deduplicate operation."""
    subset = params.get('subset')
    keep = params.get('keep', 'first')

    return lf.unique(subset=subset, keep=keep, maintain_order=True)


def _handle_explode(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle explode operation."""
    columns = params.get('columns')
    if isinstance(columns, str):
        columns = [columns]
    if not isinstance(columns, list) or not columns:
        raise ValueError('Explode requires columns parameter')
    return lf.explode(columns)


def _handle_view(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle view operation."""
    # View is a passthrough operation for visualization purposes
    # It doesn't modify the data, just allows previewing at this step
    return lf


def _handle_unpivot(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle unpivot operation."""
    # Unpivot (melt) transforms wide format to long format
    index = params.get('index') or params.get('id_vars', [])
    on = params.get('on') or params.get('value_vars')
    variable_name = params.get('variable_name', 'variable')
    value_name = params.get('value_name', 'value')

    return lf.unpivot(
        index=index,
        on=on,
        variable_name=variable_name,
        value_name=value_name,
    )


def _handle_join(lf: pl.LazyFrame, params: dict, right_lf: pl.LazyFrame | None = None) -> pl.LazyFrame:
    """Handle join operation with support for multiple join columns and column selection.

    Args:
        lf: The left LazyFrame (from parent step or main datasource)
        params: Join parameters including join_columns, right_columns, etc.
        right_lf: Optional right LazyFrame for cross-datasource joins. If None, self-join is performed.
    """
    right_source = params.get('right_source')
    how = params.get('how', 'inner')
    suffix = params.get('suffix', '_right')

    join_columns = params.get('join_columns', [])
    right_columns = params.get('right_columns', [])

    if join_columns:
        left_on = [col['left_column'] for col in join_columns if col.get('left_column')]
        right_on = [col['right_column'] for col in join_columns if col.get('right_column')]
    else:
        left_on = params.get('left_on', [])
        right_on = params.get('right_on', [])

    if not left_on or not right_on:
        raise ValueError('Join requires at least one join column pair')

    if how == 'cross':
        joined = lf.join(right_lf, how='cross') if right_lf is not None else lf.join(lf, how='cross')
    else:
        joined = (
            lf.join(right_lf, left_on=left_on, right_on=right_on, how=how, suffix=suffix)
            if right_lf is not None and right_source
            else lf.join(lf, left_on=left_on, right_on=right_on, how=how, suffix=suffix)
        )

    if right_columns and how != 'cross':
        all_columns = joined.collect_schema().names()

        final_columns = []
        for col in all_columns:
            if col.endswith(suffix):
                base_name = col[: -len(suffix)]
                if base_name in right_columns:
                    final_columns.append(col)
            else:
                final_columns.append(col)

        if final_columns != all_columns:
            return joined.select(final_columns)

    return joined


def _handle_sample(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle sample operation."""
    fraction = params.get('fraction')
    seed = params.get('seed')

    mod = int(1 / fraction)

    lf_sampled = (
        lf.with_row_index('idx')  # or with_row_count on older versions
        .filter(pl.col('idx').hash(seed=seed) % mod == 0)
        .drop('idx')
    )

    return lf_sampled


def _handle_limit(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle limit operation."""
    n = params.get('n', 10)
    return lf.head(n)


def _handle_topk(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle topk operation."""
    column = params.get('column')
    k = params.get('k', 10)
    descending = params.get('descending', False)

    if not column:
        raise ValueError('TopK requires a column parameter')

    return lf.sort(column, descending=descending).head(k)


def _handle_null_count(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle null_count operation."""
    df = lf.collect()
    null_counts = df.null_count()
    return null_counts.lazy()


def _handle_value_counts(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle value_counts operation."""
    column = params.get('column')
    normalize = params.get('normalize', False)
    sort = params.get('sort', True)

    if not column:
        raise ValueError('Value counts requires a column parameter')

    df = lf.collect()
    result = df.select(pl.col(column).value_counts(normalize=normalize, sort=sort))
    return result.lazy()


def _handle_export(lf: pl.LazyFrame, params: dict) -> pl.LazyFrame:
    """Handle export operation."""
    # Export is a passthrough operation - the actual export is triggered
    # via the /compute/export endpoint, not during pipeline execution
    return lf


def _handle_union_by_name(
    lf: pl.LazyFrame,
    params: dict,
    right_sources: dict[str, pl.LazyFrame],
) -> pl.LazyFrame:
    """Handle union_by_name operation."""
    sources = params.get('sources', [])
    allow_missing = params.get('allow_missing', True)

    if not sources:
        raise ValueError('Union by name requires at least one datasource')

    frames: list[pl.LazyFrame] = [lf]
    for source_id in sources:
        frame = right_sources.get(source_id)
        if frame is None:
            raise ValueError(f'Union by name requires datasource {source_id}')
        frames.append(frame)

    if not allow_missing:
        base_columns = lf.collect_schema().names()
        base_set = set(base_columns)
        aligned = [lf]
        for frame in frames[1:]:
            frame_columns = frame.collect_schema().names()
            if set(frame_columns) != base_set:
                raise ValueError('Union by name requires matching columns when allow_missing is false')
            aligned.append(frame.select(base_columns))
        return pl.concat(aligned, how='vertical')

    return pl.concat(frames, how='diagonal')


def get_operation_handlers() -> dict:
    """Return registry of all operation handlers."""
    return {
        'filter': _handle_filter,
        'select': _handle_select,
        'groupby': _handle_groupby,
        'sort': _handle_sort,
        'rename': _handle_rename,
        'with_columns': _handle_with_columns,
        'drop': _handle_drop,
        'pivot': _handle_pivot,
        'timeseries': _handle_timeseries,
        'string_transform': _handle_string_transform,
        'fill_null': _handle_fill_null,
        'deduplicate': _handle_deduplicate,
        'explode': _handle_explode,
        'view': _handle_view,
        'unpivot': _handle_unpivot,
        'join': _handle_join,
        'sample': _handle_sample,
        'limit': _handle_limit,
        'topk': _handle_topk,
        'null_count': _handle_null_count,
        'value_counts': _handle_value_counts,
        'export': _handle_export,
        'union_by_name': _handle_union_by_name,
    }
