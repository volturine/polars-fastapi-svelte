import polars as pl
import pytest

from modules.compute.registries.aggregations import get_aggregation
from modules.compute.registries.exports import get_export_format
from modules.compute.registries.fill_strategies import get_fill_strategy
from modules.compute.registries.operators import get_operator
from modules.compute.registries.timeseries import get_duration, get_extractor
from modules.compute.registries.types import cast_value, get_polars_type


def test_get_operator():
    op = get_operator('==')
    expr = op(pl.col('a'), 1)
    assert isinstance(expr, pl.Expr)


def test_get_operator_invalid():
    with pytest.raises(ValueError, match='Unsupported filter operator'):
        get_operator('nope')


def test_get_aggregation():
    agg = get_aggregation('sum')
    expr = agg('value')
    assert isinstance(expr, pl.Expr)


def test_get_aggregation_invalid():
    with pytest.raises(ValueError, match='Unsupported aggregation'):
        get_aggregation('nope')


def test_timeseries_extractor_and_duration():
    assert get_extractor('year') == 'year'
    duration = get_duration('days', 2)
    assert isinstance(duration, pl.Expr)


def test_timeseries_extractor_invalid():
    with pytest.raises(ValueError, match='Unsupported time component'):
        get_extractor('nope')


def test_timeseries_duration_invalid():
    with pytest.raises(ValueError, match='Unsupported duration unit'):
        get_duration('nope', 1)


def test_fill_strategy():
    strategy = get_fill_strategy('forward')
    assert strategy is not None


def test_export_format():
    fmt = get_export_format('csv')
    assert fmt.extension == '.csv'
    assert fmt.content_type == 'text/csv'


def test_export_format_invalid():
    with pytest.raises(ValueError, match='Unsupported export format'):
        get_export_format('nope')


def test_type_casting():
    assert cast_value('1', 'Int64') == 1
    assert get_polars_type('Float64') == pl.Float64
