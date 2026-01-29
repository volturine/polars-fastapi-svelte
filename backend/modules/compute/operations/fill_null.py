import polars as pl

from modules.compute.operations.base import OperationHandler, OperationParams
from modules.compute.registries.fill_strategies import get_fill_strategy
from modules.compute.registries.types import cast_value, get_polars_type


class FillNullParams(OperationParams):
    strategy: str
    columns: list[str] | None = None
    value: str | int | float | bool | None = None
    value_type: str | None = None


class FillNullHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'fill_null'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = FillNullParams.model_validate(params)
        columns = validated.columns

        if validated.strategy == 'literal':
            value = cast_value(validated.value, validated.value_type)
            dtype = get_polars_type(validated.value_type)

            def build_expr(col: str) -> pl.Expr:
                expr = pl.col(col)
                if dtype is not None:
                    expr = expr.cast(dtype)
                return expr.fill_null(value)

            if columns:
                return lf.with_columns([build_expr(col) for col in columns])
            return lf.with_columns([build_expr(col) for col in lf.columns])

        if validated.strategy in {'forward', 'backward', 'mean', 'median', 'zero'}:
            strategy = get_fill_strategy(validated.strategy)
            if not strategy:
                raise ValueError(f'Unsupported fill_null strategy: {validated.strategy}')
            if columns:
                return lf.with_columns([strategy(pl.col(col)) for col in columns])
            return lf.with_columns([strategy(pl.col(col)) for col in lf.columns])

        if validated.strategy == 'drop_rows':
            if columns:
                return lf.drop_nulls(subset=columns)
            return lf.drop_nulls()

        raise ValueError(f'Unsupported fill_null strategy: {validated.strategy}')
