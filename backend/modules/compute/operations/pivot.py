from typing import Literal

import polars as pl

from modules.compute.core.base import OperationHandler, OperationParams


class PivotParams(OperationParams):
    index: list[str]
    columns: str
    values: str | None = None
    aggregate_function: Literal['first', 'last', 'sum', 'mean', 'median', 'min', 'max', 'count'] = 'first'
    on_columns: list[str] | None = None


class PivotHandler(OperationHandler):
    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        **_,
    ) -> pl.LazyFrame:
        validated = PivotParams.model_validate(params)

        if not validated.columns:
            raise ValueError('Pivot requires a pivot column')

        if not validated.index:
            raise ValueError('Pivot requires at least one index column')

        # on_columns expects unique *values* from the pivot column, not column names.
        # When not provided, compute from the data.
        on_columns = validated.on_columns or params.get('onColumns')
        if not on_columns:
            on_columns = lf.select(validated.columns).collect().to_series().unique().sort().to_list()

        agg = None if validated.aggregate_function == 'count' else validated.aggregate_function
        return lf.pivot(
            on=validated.columns,
            on_columns=on_columns,
            index=validated.index,
            aggregate_function=agg,
            values=validated.values,
        )
