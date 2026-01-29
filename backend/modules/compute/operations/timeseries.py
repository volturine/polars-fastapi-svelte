import polars as pl

from modules.compute.operations.base import OperationHandler, OperationParams
from modules.compute.registries.timeseries import get_duration, get_extractor


class TimeseriesParams(OperationParams):
    column: str
    operation_type: str
    new_column: str
    component: str | None = None
    value: int | float | None = None
    unit: str | None = None
    direction: str | None = None
    column2: str | None = None


class TimeseriesHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'timeseries'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = TimeseriesParams.model_validate(params)

        if validated.operation_type == 'extract':
            method = get_extractor(validated.component or '')
            return lf.with_columns(getattr(pl.col(validated.column).dt, method)().alias(validated.new_column))

        if validated.operation_type in {'add', 'subtract', 'offset'}:
            if validated.value is None:
                raise ValueError('timeseries operation requires numeric value parameter')
            if not validated.unit:
                raise ValueError('timeseries operation requires unit parameter')

            if validated.unit == 'months':
                if validated.operation_type == 'subtract' or validated.direction == 'subtract':
                    return lf.with_columns(pl.col(validated.column).dt.offset_by(f'-{validated.value}mo').alias(validated.new_column))
                return lf.with_columns(pl.col(validated.column).dt.offset_by(f'{validated.value}mo').alias(validated.new_column))

            duration = get_duration(validated.unit, int(validated.value))
            subtracting = validated.operation_type == 'subtract' or validated.direction == 'subtract'
            expr = pl.col(validated.column) - duration if subtracting else pl.col(validated.column) + duration
            return lf.with_columns(expr.alias(validated.new_column))

        if validated.operation_type == 'diff':
            if not validated.column2:
                raise ValueError('timeseries operation requires column2 parameter')
            return lf.with_columns((pl.col(validated.column2) - pl.col(validated.column)).alias(validated.new_column))

        raise ValueError(f'Unsupported timeseries operation: {validated.operation_type}')
