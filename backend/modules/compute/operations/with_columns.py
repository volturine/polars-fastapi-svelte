"""With columns operation for adding/modifying columns."""

from typing import Any

import polars as pl
from pydantic import BaseModel, ConfigDict, Field

from modules.compute.core.base import OperationHandler, OperationParams


class WithColumnsExpr(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str
    type: str
    value: Any | None = None
    column: str | None = None
    args: list[str] | None = None
    code: str | None = None


class WithColumnsParams(OperationParams):
    expressions: list[WithColumnsExpr] = Field(default_factory=list)


class WithColumnsHandler(OperationHandler):
    """Add or modify columns using expressions."""

    @property
    def name(self) -> str:
        return 'with_columns'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = WithColumnsParams.model_validate(params)
        exprs: list[pl.Expr] = []
        for expr in validated.expressions:
            if expr.type == 'literal':
                exprs.append(pl.lit(expr.value).alias(expr.name))
            elif expr.type == 'column' and expr.column:
                exprs.append(pl.col(expr.column).alias(expr.name))
            elif expr.type == 'udf' and expr.code:
                scope: dict[str, Any] = {'pl': pl, '__builtins__': __builtins__}
                local_scope: dict[str, Any] = {}
                exec(expr.code, scope, local_scope)
                udf = local_scope.get('udf') or scope.get('udf')
                if not callable(udf):
                    raise ValueError('UDF must define a callable named udf')
                args = expr.args or []
                if args:
                    struct = pl.struct(args)
                    exprs.append(struct.map_elements(lambda row: udf(*[row[col] for col in args])).alias(expr.name))
                else:
                    exprs.append(pl.lit(0).map_elements(lambda _: udf()).alias(expr.name))
        return lf.with_columns(exprs)
