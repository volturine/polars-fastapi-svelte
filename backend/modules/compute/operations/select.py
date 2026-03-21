"""Select columns operation."""

from typing import Literal

import polars as pl
from pydantic import Field

from modules.compute.core.base import OperationHandler, OperationParams
from modules.compute.operations.type_casting import require_polars_type


class SelectParams(OperationParams):
    columns: list[str]
    cast_map: dict[str, Literal['Int64', 'Float64', 'Boolean', 'String', 'Utf8', 'Date', 'Datetime']] = Field(default_factory=dict)


class SelectHandler(OperationHandler):
    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        **_,
    ) -> pl.LazyFrame:
        validated = SelectParams.model_validate(params)
        missing = sorted(set(validated.cast_map) - set(validated.columns))
        if missing:
            cols = ', '.join(missing)
            raise ValueError(f'cast_map keys must reference selected columns. Unknown keys: {cols}')
        selected = lf.select(validated.columns)
        if not validated.cast_map:
            return selected
        exprs = [pl.col(col).cast(require_polars_type(dtype)).alias(col) for col, dtype in validated.cast_map.items()]
        return selected.with_columns(exprs)
