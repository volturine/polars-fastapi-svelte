from collections.abc import Callable

import polars as pl

AGG_FUNCTIONS: dict[str, Callable[[str], pl.Expr]] = {
    'sum': lambda col: pl.col(col).sum(),
    'mean': lambda col: pl.col(col).mean(),
    'count': lambda col: pl.col(col).count(),
    'min': lambda col: pl.col(col).min(),
    'max': lambda col: pl.col(col).max(),
    'first': lambda col: pl.col(col).first(),
    'last': lambda col: pl.col(col).last(),
    'median': lambda col: pl.col(col).median(),
    'std': lambda col: pl.col(col).std(),
    'var': lambda col: pl.col(col).var(),
    'collect_list': lambda col: pl.col(col).implode(),
    'collect_set': lambda col: pl.col(col).implode().list.unique(),
}


def get_aggregation(name: str) -> Callable[[str], pl.Expr]:
    agg = AGG_FUNCTIONS.get(name)
    if not agg:
        raise ValueError(f'Unsupported aggregation function: {name}')
    return agg
