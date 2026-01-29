from typing import Any, Literal

import polars as pl
from pydantic import BaseModel, ConfigDict

from modules.compute.operations.base import OperationHandler, OperationParams


class SelectParams(OperationParams):
    columns: list[str]


class SelectHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'select'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = SelectParams.model_validate(params)
        return lf.select(validated.columns)


class SortParams(OperationParams):
    columns: list[str]
    descending: list[bool] | bool = False


class SortHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'sort'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = SortParams.model_validate(params)
        descending = validated.descending
        columns = validated.columns
        if isinstance(descending, list) and len(descending) != len(columns):
            if len(descending) > len(columns):
                descending = descending[: len(columns)]
            else:
                descending = descending + [False] * (len(columns) - len(descending))
        return lf.sort(columns, descending=descending)


class RenameParams(OperationParams):
    mapping: dict[str, str]


class RenameHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'rename'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = RenameParams.model_validate(params)
        return lf.rename(validated.mapping)


class DropParams(OperationParams):
    columns: list[str]


class DropHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'drop'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = DropParams.model_validate(params)
        return lf.drop(validated.columns)


class WithColumnsExpr(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str
    type: str
    value: Any | None = None
    column: str | None = None


class WithColumnsParams(OperationParams):
    expressions: list[WithColumnsExpr]


class WithColumnsHandler(OperationHandler):
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
                continue
            if expr.type == 'column' and expr.column:
                exprs.append(pl.col(expr.column).alias(expr.name))
        return lf.with_columns(exprs)


class DeduplicateParams(OperationParams):
    subset: list[str] | None = None
    keep: Literal['first', 'last', 'any', 'none'] = 'first'


class DeduplicateHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'deduplicate'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = DeduplicateParams.model_validate(params)
        return lf.unique(subset=validated.subset, keep=validated.keep, maintain_order=True)


class ExplodeParams(OperationParams):
    columns: list[str] | str


class ExplodeHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'explode'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = ExplodeParams.model_validate(params)
        columns = validated.columns
        if isinstance(columns, str):
            columns = [columns]
        if not columns:
            raise ValueError('Explode requires columns parameter')
        return lf.explode(columns)


class UnpivotParams(OperationParams):
    index: list[str] | None = None
    id_vars: list[str] | None = None
    on: list[str] | None = None
    value_vars: list[str] | None = None
    variable_name: str = 'variable'
    value_name: str = 'value'


class UnpivotHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'unpivot'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = UnpivotParams.model_validate(params)
        index = validated.index or validated.id_vars or []
        on = validated.on or validated.value_vars
        return lf.unpivot(
            index=index,
            on=on,
            variable_name=validated.variable_name,
            value_name=validated.value_name,
        )


class SampleParams(OperationParams):
    fraction: float
    seed: int | None = None


class SampleHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'sample'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = SampleParams.model_validate(params)
        if validated.fraction <= 0 or validated.fraction > 1:
            raise ValueError('Sample requires fraction between 0 and 1')
        mod = int(1 / validated.fraction)
        if validated.seed is not None:
            seed = validated.seed
            return lf.with_row_index('idx').filter(pl.col('idx').hash(seed=seed) % mod == 0).drop('idx')
        return lf.with_row_index('idx').filter(pl.col('idx').hash() % mod == 0).drop('idx')


class LimitParams(OperationParams):
    n: int = 10


class LimitHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'limit'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = LimitParams.model_validate(params)
        return lf.head(validated.n)


class TopKParams(OperationParams):
    column: str
    k: int = 10
    descending: bool = False


class TopKHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'topk'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = TopKParams.model_validate(params)
        return lf.sort(validated.column, descending=validated.descending).head(validated.k)


class NullCountParams(OperationParams):
    pass


class NullCountHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'null_count'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        _ = NullCountParams.model_validate(params)
        df = lf.collect()
        return df.null_count().lazy()


class ValueCountsParams(OperationParams):
    column: str
    normalize: bool = False
    sort: bool = True


class ValueCountsHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'value_counts'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        validated = ValueCountsParams.model_validate(params)
        df = lf.collect()
        result = df.select(pl.col(validated.column).value_counts(normalize=validated.normalize, sort=validated.sort))
        return result.lazy()


class ViewParams(OperationParams):
    rowLimit: int | None = None


class ViewHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'view'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        _ = ViewParams.model_validate(params)
        return lf


class ExportParams(OperationParams):
    format: str = 'csv'
    filename: str = 'export'
    destination: str = 'download'


class ExportHandler(OperationHandler):
    @property
    def name(self) -> str:
        return 'export'

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        *,
        right_lf: pl.LazyFrame | None = None,
        right_sources: dict[str, pl.LazyFrame] | None = None,
    ) -> pl.LazyFrame:
        _ = ExportParams.model_validate(params)
        return lf
