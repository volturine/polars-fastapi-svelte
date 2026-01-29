from collections.abc import Callable
from typing import Any

import polars as pl

FILTER_OPERATORS: dict[str, Callable[[pl.Expr, Any], pl.Expr]] = {
    '=': lambda col, value: col == value,
    '==': lambda col, value: col == value,
    '!=': lambda col, value: col != value,
    '>': lambda col, value: col > value,
    '<': lambda col, value: col < value,
    '>=': lambda col, value: col >= value,
    '<=': lambda col, value: col <= value,
    'contains': lambda col, value: col.str.contains(value),
    'starts_with': lambda col, value: col.str.starts_with(value),
    'ends_with': lambda col, value: col.str.ends_with(value),
    'is_null': lambda col, _: col.is_null(),
    'is_not_null': lambda col, _: col.is_not_null(),
    'in': lambda col, value: col.is_in(value),
    'not_in': lambda col, value: ~col.is_in(value),
}


def get_operator(name: str) -> Callable[[pl.Expr, Any], pl.Expr]:
    op = FILTER_OPERATORS.get(name)
    if not op:
        raise ValueError(f'Unsupported filter operator: {name}')
    return op
