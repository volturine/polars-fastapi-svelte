from typing import Any

import polars as pl
from pydantic import BaseModel, ConfigDict

from modules.compute.operations.base import OperationHandler, OperationParams
from modules.compute.registries.operators import get_operator


class FilterCondition(BaseModel):
    model_config = ConfigDict(extra='forbid')

    column: str
    operator: str = '=='
    value: Any | None = None


class FilterParams(OperationParams):
    conditions: list[FilterCondition]
    logic: str = 'AND'


class FilterHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'filter'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = FilterParams.model_validate(params)

        exprs: list[pl.Expr] = []
        for cond in validated.conditions:
            op = get_operator(cond.operator)
            exprs.append(op(pl.col(cond.column), cond.value))

        if len(exprs) == 1:
            return lf.filter(exprs[0])

        if validated.logic == 'AND':
            combined = exprs[0]
            for expr in exprs[1:]:
                combined = combined & expr
            return lf.filter(combined)

        if validated.logic == 'OR':
            combined = exprs[0]
            for expr in exprs[1:]:
                combined = combined | expr
            return lf.filter(combined)

        raise ValueError(f'Unsupported logic operator: {validated.logic}')
