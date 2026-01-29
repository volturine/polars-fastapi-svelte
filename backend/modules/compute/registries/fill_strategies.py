from collections.abc import Callable

import polars as pl

FILL_STRATEGIES: dict[str, Callable[[pl.Expr], pl.Expr]] = {
    'forward': lambda col: col.forward_fill(),
    'backward': lambda col: col.backward_fill(),
    'mean': lambda col: col.fill_null(col.mean()),
    'median': lambda col: col.fill_null(col.median()),
    'zero': lambda col: col.fill_null(0),
}


def get_fill_strategy(name: str) -> Callable[[pl.Expr], pl.Expr] | None:
    return FILL_STRATEGIES.get(name)
