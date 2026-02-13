from typing import Literal

import polars as pl
from pydantic import ConfigDict

from modules.compute.core.base import OperationHandler, OperationParams


class ChartParams(OperationParams):
    model_config = ConfigDict(extra='forbid')

    chart_type: Literal['bar', 'histogram', 'scatter', 'line', 'pie', 'boxplot'] = 'bar'
    x_column: str
    y_column: str | None = None
    bins: int = 10
    aggregation: Literal['sum', 'mean', 'count', 'min', 'max'] = 'sum'
    group_column: str | None = None


class ChartHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'chart'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        ChartParams.model_validate(params)
        return lf
