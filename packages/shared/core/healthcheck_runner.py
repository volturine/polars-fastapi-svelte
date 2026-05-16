import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeAlias

import polars as pl
from sqlmodel import Session

from contracts.healthcheck_models import HealthCheck, HealthCheckResult, HealthCheckType

HealthcheckDetails: TypeAlias = dict[str, object]
HealthcheckEvaluator: TypeAlias = Callable[[HealthCheck, pl.DataFrame], tuple[bool, str, HealthcheckDetails]]


def _build_expressions(checks: list[HealthCheck], schema_names: set[str]) -> tuple[list[pl.Expr], list[HealthCheck]]:
    """Build Polars aggregation expressions for all valid checks.

    Returns (expressions, valid_checks). Checks whose referenced column is
    missing from the schema are excluded so the caller can create immediate-
    failure results for them.
    """
    exprs: list[pl.Expr] = []
    valid: list[HealthCheck] = []

    sorted_names = sorted(schema_names)
    row_count_added = False

    for check in checks:
        config = check.config
        if check.check_type_kind() == HealthCheckType.ROW_COUNT:
            valid.append(check)
            if row_count_added:
                continue
            exprs.append(pl.len().alias('row_count__count'))
            row_count_added = True

        elif check.check_type_kind() == HealthCheckType.COLUMN_NULL:
            col = str(config.get('column', ''))
            if col not in schema_names:
                continue
            prefix = check.id
            pct = pl.col(col).null_count().cast(pl.Float64) / pl.len().cast(pl.Float64) * 100.0
            exprs.append(pct.alias(f'{prefix}__null_pct'))
            valid.append(check)

        elif check.check_type_kind() == HealthCheckType.COLUMN_UNIQUE:
            col = str(config.get('column', ''))
            if col not in schema_names:
                continue
            prefix = check.id
            exprs.append(pl.col(col).n_unique().alias(f'{prefix}__unique'))
            valid.append(check)

        elif check.check_type_kind() == HealthCheckType.COLUMN_RANGE:
            col = str(config.get('column', ''))
            if col not in schema_names:
                continue
            prefix = check.id
            exprs.append(pl.col(col).min().alias(f'{prefix}__min'))
            exprs.append(pl.col(col).max().alias(f'{prefix}__max'))
            valid.append(check)

        elif check.check_type_kind() == HealthCheckType.COLUMN_COUNT:
            valid.append(check)

        elif check.check_type_kind() == HealthCheckType.NULL_PERCENTAGE:
            threshold = float(config.get('threshold', 0))
            if threshold < 0:
                continue
            if not sorted_names:
                exprs.append(pl.lit(0.0).alias(f'{check.id}__null_pct'))
                valid.append(check)
                continue
            nulls = sum(pl.col(name).null_count().cast(pl.Float64) for name in sorted_names)
            total = pl.len().cast(pl.Float64) * float(len(sorted_names))
            pct = (nulls / total * 100.0).fill_nan(0.0)
            exprs.append(pct.alias(f'{check.id}__null_pct'))
            valid.append(check)

        elif check.check_type_kind() == HealthCheckType.DUPLICATE_PERCENTAGE:
            cols = config.get('columns')
            columns = [str(col) for col in cols] if isinstance(cols, list) else []
            if not columns:
                columns = sorted_names
            if any(col not in schema_names for col in columns):
                continue
            prefix = check.id
            exprs.append(pl.len().alias(f'{prefix}__rows'))
            exprs.append(pl.struct(columns).n_unique().alias(f'{prefix}__unique_rows'))
            valid.append(check)

    return exprs, valid


def _evaluate_row_count(check: HealthCheck, row: pl.DataFrame) -> tuple[bool, str, HealthcheckDetails]:
    config = check.config
    if 'row_count__count' in row.columns:
        count: int = row['row_count__count'][0]
    else:
        count = row[f'{check.id}__count'][0]
    min_rows = config.get('min_rows')
    max_rows = config.get('max_rows')

    passed = True
    messages: list[str] = []
    if min_rows is not None and count < int(min_rows):
        passed = False
        messages.append(f'Too few: {count} < {min_rows}')
    if max_rows is not None and count > int(max_rows):
        passed = False
        messages.append(f'Too many: {count} > {max_rows}')

    message = '; '.join(messages) if messages else f'Row count: {count}'
    details: HealthcheckDetails = {**config, 'actual_count': count}
    return passed, message, details


def _evaluate_column_count(check: HealthCheck, schema_names: set[str]) -> tuple[bool, str, HealthcheckDetails]:
    config = check.config
    count = len(schema_names)
    min_cols = config.get('min_columns')
    max_cols = config.get('max_columns')

    passed = True
    messages: list[str] = []
    if min_cols is not None and count < int(min_cols):
        passed = False
        messages.append(f'Too few: {count} < {min_cols}')
    if max_cols is not None and count > int(max_cols):
        passed = False
        messages.append(f'Too many: {count} > {max_cols}')

    message = '; '.join(messages) if messages else f'Column count: {count}'
    details: HealthcheckDetails = {**config, 'actual_count': count}
    return passed, message, details


def _evaluate_column_null(check: HealthCheck, row: pl.DataFrame) -> tuple[bool, str, HealthcheckDetails]:
    config = check.config
    pct: float = row[f'{check.id}__null_pct'][0]
    threshold = float(config.get('threshold', 0))

    passed = pct <= threshold
    message = f'Nulls: {pct:.1f}% (threshold: {threshold}%)'
    details: HealthcheckDetails = {**config, 'actual_percentage': round(pct, 2)}
    return passed, message, details


def _evaluate_null_percentage(check: HealthCheck, row: pl.DataFrame) -> tuple[bool, str, HealthcheckDetails]:
    config = check.config
    pct: float = row[f'{check.id}__null_pct'][0]
    threshold = float(config.get('threshold', 0))

    passed = pct <= threshold
    message = f'Nulls: {pct:.1f}% (threshold: {threshold}%)'
    details: HealthcheckDetails = {**config, 'actual_percentage': round(pct, 2)}
    return passed, message, details


def _evaluate_column_unique(check: HealthCheck, row: pl.DataFrame) -> tuple[bool, str, HealthcheckDetails]:
    config = check.config
    unique: int = row[f'{check.id}__unique'][0]
    expected_raw = config.get('expected_unique')
    expected = int(expected_raw) if expected_raw is not None else None

    if expected is None:
        passed = True
        message = f'Unique values: {unique}'
    else:
        passed = unique == expected
        message = f'Unique: {unique} (expected: {expected})'

    details: HealthcheckDetails = {**config, 'actual_unique': unique}
    return passed, message, details


def _evaluate_column_range(check: HealthCheck, row: pl.DataFrame) -> tuple[bool, str, HealthcheckDetails]:
    config = check.config
    col_min = row[f'{check.id}__min'][0]
    col_max = row[f'{check.id}__max'][0]
    min_value = config.get('min')
    max_value = config.get('max')

    passed = True
    messages: list[str] = []
    if min_value is not None and col_min < float(min_value):
        passed = False
        messages.append(f'Min {col_min!r} < {min_value}')
    if max_value is not None and col_max > float(max_value):
        passed = False
        messages.append(f'Max {col_max!r} > {max_value}')

    message = '; '.join(messages) if messages else f'Range: [{col_min!r}, {col_max!r}]'
    details: HealthcheckDetails = {**config, 'actual_min': col_min, 'actual_max': col_max}
    return passed, message, details


def _evaluate_duplicate_percentage(check: HealthCheck, row: pl.DataFrame) -> tuple[bool, str, HealthcheckDetails]:
    config = check.config
    total: int = row[f'{check.id}__rows'][0]
    unique: int = row[f'{check.id}__unique_rows'][0]
    threshold = float(config.get('threshold', 0))

    pct = 0.0 if total == 0 else (1 - unique / total) * 100.0

    passed = pct <= threshold
    message = f'Duplicates: {pct:.1f}% (threshold: {threshold}%)'
    details: HealthcheckDetails = {**config, 'actual_percentage': round(pct, 2)}
    return passed, message, details


_EVALUATORS: dict[HealthCheckType, HealthcheckEvaluator] = {
    HealthCheckType.ROW_COUNT: _evaluate_row_count,
    HealthCheckType.COLUMN_NULL: _evaluate_column_null,
    HealthCheckType.NULL_PERCENTAGE: _evaluate_null_percentage,
    HealthCheckType.COLUMN_UNIQUE: _evaluate_column_unique,
    HealthCheckType.COLUMN_RANGE: _evaluate_column_range,
    HealthCheckType.DUPLICATE_PERCENTAGE: _evaluate_duplicate_percentage,
}


def run_healthchecks(session: Session, checks: list[HealthCheck], lf: pl.LazyFrame, *, critical_only: bool = False) -> list[HealthCheckResult]:
    """Run all health checks in a single LazyFrame evaluation."""
    selected = checks
    if critical_only:
        selected = [check for check in checks if check.critical]
    if not selected:
        return []

    now = datetime.now(UTC)
    schema_names = set(lf.collect_schema().names())
    exprs, valid_checks = _build_expressions(selected, schema_names)

    valid_ids = {c.id for c in valid_checks}
    results: list[HealthCheckResult] = []
    for check in selected:
        if check.id in valid_ids:
            continue
        col = check.config.get('column', '')
        result = HealthCheckResult(
            id=str(uuid.uuid4()),
            healthcheck_id=check.id,
            passed=False,
            message=f'Column "{col}" not found in dataset',
            details={**check.config, 'error': 'column_not_found'},
            checked_at=now,
        )
        session.add(result)
        results.append(result)

    collected = lf.select(exprs).collect() if exprs else None
    for check in valid_checks:
        check_type = check.check_type_kind()
        evaluator = _EVALUATORS.get(check_type)
        if check_type == HealthCheckType.COLUMN_COUNT:
            passed, message, details = _evaluate_column_count(check, schema_names)
        elif collected is None or not evaluator:
            passed, message, details = False, f'Unknown check type: {check.check_type}', check.config
        else:
            passed, message, details = evaluator(check, collected)

        result = HealthCheckResult(id=str(uuid.uuid4()), healthcheck_id=check.id, passed=passed, message=message, details=details, checked_at=now)
        session.add(result)
        results.append(result)

    session.commit()
    return results
