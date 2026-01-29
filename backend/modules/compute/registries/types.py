from collections.abc import Callable
from typing import Any

import polars as pl

TYPE_CASTERS: dict[str, tuple[Callable[[Any], Any] | None, pl.DataType]] = {
    'Int64': (int, pl.Int64),
    'Float64': (float, pl.Float64),
    'Boolean': (bool, pl.Boolean),
    'String': (str, pl.Utf8),
    'Utf8': (str, pl.Utf8),
    'Date': (None, pl.Date),
    'Datetime': (None, pl.Datetime),
}


def cast_value(value: Any, type_name: str | None) -> Any:
    if not type_name or value is None:
        return value
    spec = TYPE_CASTERS.get(type_name)
    if not spec:
        return value
    caster, _ = spec
    return caster(value) if caster else value


def get_polars_type(type_name: str | None) -> pl.DataType | None:
    if not type_name:
        return None
    spec = TYPE_CASTERS.get(type_name)
    return spec[1] if spec else None
