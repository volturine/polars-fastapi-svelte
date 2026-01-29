import polars as pl
from pydantic import BaseModel, ConfigDict

from modules.compute.operations.base import OperationHandler, OperationParams
from modules.compute.registries.aggregations import get_aggregation


class AggregationSpec(BaseModel):
    model_config = ConfigDict(extra='forbid')

    column: str
    function: str
    alias: str | None = None


class GroupByParams(OperationParams):
    group_by: list[str]
    aggregations: list[AggregationSpec]


class GroupByHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'groupby'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = GroupByParams.model_validate(params)
        exprs: list[pl.Expr] = []
        for agg in validated.aggregations:
            expr = get_aggregation(agg.function)(agg.column)
            alias = agg.alias or f'{agg.column}_{agg.function}'
            exprs.append(expr.alias(alias))
        return lf.group_by(validated.group_by).agg(exprs)
