from collections.abc import Callable

import polars as pl

DT_EXTRACTORS: dict[str, str] = {
    'year': 'year',
    'month': 'month',
    'day': 'day',
    'hour': 'hour',
    'minute': 'minute',
    'second': 'second',
    'quarter': 'quarter',
    'week': 'week',
    'dayofweek': 'weekday',
}

DURATION_BUILDERS: dict[str, Callable[[int], pl.Expr]] = {
    'seconds': lambda value: pl.duration(seconds=value),
    'minutes': lambda value: pl.duration(minutes=value),
    'hours': lambda value: pl.duration(hours=value),
    'days': lambda value: pl.duration(days=value),
    'weeks': lambda value: pl.duration(weeks=value),
}


def get_extractor(component: str) -> str:
    method = DT_EXTRACTORS.get(component)
    if not method:
        raise ValueError(f'Unsupported time component: {component}')
    return method


def get_duration(unit: str, value: int) -> pl.Expr:
    builder = DURATION_BUILDERS.get(unit)
    if not builder:
        raise ValueError(f'Unsupported duration unit: {unit}')
    return builder(value)
