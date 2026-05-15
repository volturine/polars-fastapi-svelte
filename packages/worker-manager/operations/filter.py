from collections.abc import Callable
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import polars as pl
from contracts.compute.base import OperationHandler, OperationParams
from contracts.enums import DataForgeStrEnum
from core.config import settings
from pydantic import BaseModel, ConfigDict, Field, model_validator

from operations.validation import validate_regex_pattern


class FilterValueType(DataForgeStrEnum):
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    COLUMN = "column"
    BOOLEAN = "boolean"

    @staticmethod
    def parse_datetime(value: str) -> datetime:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        if " " in value and "T" not in value:
            raise ValueError(
                f"Cannot parse datetime string '{value}'. Accepted format: ISO 8601 (for example 2024-06-15T12:30:00)",
            )
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            raise ValueError(
                f"Cannot parse datetime string '{value}'. Accepted format: ISO 8601 (for example 2024-06-15T12:30:00)",
            ) from None

    def coerce(self, value: Any) -> Any:
        if value is None:
            return None

        if isinstance(value, list):
            return [self.coerce(item) for item in value]

        if self == FilterValueType.NUMBER:
            if isinstance(value, (int, float)):
                return value
            text = str(value)
            parsed = float(text)
            if parsed.is_integer() and "." not in text and "e" not in text.lower():
                return int(parsed)
            return parsed

        if self == FilterValueType.BOOLEAN:
            if isinstance(value, bool):
                return value
            return str(value).lower() in ("true", "1", "yes")

        if self == FilterValueType.DATE:
            if isinstance(value, datetime):
                return value.date()
            return self.parse_datetime(str(value)).date()

        if self == FilterValueType.DATETIME:
            parsed_dt = value if isinstance(value, datetime) else self.parse_datetime(str(value))
            if not parsed_dt.tzinfo and not settings.normalize_tz:
                return parsed_dt
            tz = ZoneInfo(settings.timezone)
            parsed_dt = parsed_dt.replace(tzinfo=tz) if not parsed_dt.tzinfo else parsed_dt.astimezone(tz)
            return parsed_dt if settings.normalize_tz else parsed_dt.replace(tzinfo=None)

        return str(value)


NULL_CHECK_OPERATORS = frozenset({"is_null", "is_not_null"})


class FilterCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column: str
    operator: str = "=="
    value: Any | list[Any] | None = None
    value_type: FilterValueType = FilterValueType.STRING
    compare_column: str | None = None

    @staticmethod
    def normalize_text(value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return value.strip()

    @classmethod
    def normalize_many(cls, conditions: list[Any] | None) -> list[Any]:
        if not conditions:
            return []

        normalized: list[Any] = []
        for condition in conditions:
            if not isinstance(condition, dict):
                normalized.append(condition)
                continue

            column = cls.normalize_text(condition.get("column"))
            if not column:
                continue

            operator = condition.get("operator") or "="
            value_type = condition.get("value_type", FilterValueType.STRING.value)
            item: dict[str, Any] = {
                "column": column,
                "operator": operator,
                "value": condition.get("value"),
                "value_type": value_type,
            }

            if operator in NULL_CHECK_OPERATORS:
                normalized.append(item)
                continue

            compare_column = cls.normalize_text(condition.get("compare_column"))
            if value_type == FilterValueType.COLUMN and not compare_column:
                continue
            if compare_column:
                item["compare_column"] = compare_column

            normalized.append(item)

        return normalized

    @model_validator(mode="after")
    def validate_condition(self) -> "FilterCondition":
        if self.operator in NULL_CHECK_OPERATORS:
            return self
        if self.value_type == FilterValueType.COLUMN and not self.compare_column:
            raise ValueError("compare_column required when value_type is column")
        if self.value_type != FilterValueType.COLUMN and self.value is None:
            raise ValueError("value required for non-column comparisons")
        return self


class FilterParams(OperationParams):
    conditions: list[FilterCondition] = Field(default_factory=list)
    logic: str = "AND"

    @model_validator(mode="before")
    @classmethod
    def normalize_conditions(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        return {
            **data,
            "conditions": FilterCondition.normalize_many(data.get("conditions")),
        }


class FilterHandler(OperationHandler):
    OPERATORS: dict[str, Callable[[pl.Expr, Any], pl.Expr]] = {
        "=": lambda col, val: col == val,
        "==": lambda col, val: col == val,
        "!=": lambda col, val: col != val,
        ">": lambda col, val: col > val,
        "<": lambda col, val: col < val,
        ">=": lambda col, val: col >= val,
        "<=": lambda col, val: col <= val,
        "contains": lambda col, val: col.str.contains(val, literal=True),
        "not_contains": lambda col, val: ~col.str.contains(val, literal=True),
        "starts_with": lambda col, val: col.str.starts_with(val),
        "ends_with": lambda col, val: col.str.ends_with(val),
        "regex": lambda col, val: col.str.contains(val, literal=False),
        "is_null": lambda col, _: col.is_null(),
        "is_not_null": lambda col, _: col.is_not_null(),
        "in": lambda col, val: col.is_in(val),
        "not_in": lambda col, val: ~col.is_in(val),
    }

    COLUMN_OPERATORS: dict[str, Callable[[pl.Expr, pl.Expr], pl.Expr]] = {
        "=": lambda left, right: left == right,
        "==": lambda left, right: left == right,
        "!=": lambda left, right: left != right,
        ">": lambda left, right: left > right,
        "<": lambda left, right: left < right,
        ">=": lambda left, right: left >= right,
        "<=": lambda left, right: left <= right,
    }

    def __call__(
        self,
        lf: pl.LazyFrame,
        params: dict,
        **_,
    ) -> pl.LazyFrame:
        validated = FilterParams.model_validate(params)
        if not validated.conditions:
            return lf

        schema = lf.collect_schema()

        exprs = [self._build_expr(cond, schema) for cond in validated.conditions]

        if validated.logic == "AND":
            return lf.filter(pl.all_horizontal(exprs))
        if validated.logic == "OR":
            return lf.filter(pl.any_horizontal(exprs))
        raise ValueError(f"Unsupported logic operator: {validated.logic}")

    def _build_expr(self, cond: FilterCondition, schema: pl.Schema) -> pl.Expr:
        left = pl.col(cond.column)
        col_dtype = schema.get(cond.column)
        if col_dtype:
            left = _normalize_datetime_col(left, col_dtype)

        if cond.operator in ("is_null", "is_not_null"):
            return get_operator(cond.operator)(left, None)

        if cond.value_type == FilterValueType.COLUMN:
            op = self.COLUMN_OPERATORS.get(cond.operator)
            if not op:
                raise ValueError(f"Operator {cond.operator} not supported for column comparison")
            if not cond.compare_column:
                raise ValueError("compare_column required when value_type is column")
            right = pl.col(cond.compare_column)
            if cond.compare_column in schema:
                right = _normalize_datetime_col(right, schema[cond.compare_column])
            return op(left, right)

        is_date_only = _is_date_only_value(cond.value)
        is_datetime_col = isinstance(col_dtype, pl.Datetime)

        if is_date_only and is_datetime_col and cond.value_type == "datetime":
            return get_operator(cond.operator)(pl.col(cond.column).dt.date(), FilterValueType.DATE.coerce(cond.value))

        coerced = cond.value_type.coerce(cond.value)
        op = get_operator(cond.operator)
        if cond.operator == "regex" and coerced == "":
            return pl.lit(False)
        if cond.operator == "regex" and isinstance(coerced, str):
            validate_regex_pattern(coerced)
        if isinstance(coerced, list):
            if not coerced:
                if cond.operator in ("not_contains", "not_in"):
                    return pl.lit(True)
                return pl.lit(False)
            if cond.operator in ("in", "not_in"):
                return op(left, coerced)
            if cond.operator == "not_contains":
                combined = op(left, coerced[0])
                for item in coerced[1:]:
                    combined = combined & op(left, item)
                return combined
            combined = op(left, coerced[0])
            for item in coerced[1:]:
                combined = combined | op(left, item)
            return combined
        return op(left, coerced)


def _is_date_only_value(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return len(value) == 10 and "-" in value and "T" not in value


def _normalize_datetime_col(expr: pl.Expr, dtype: pl.DataType) -> pl.Expr:
    if not isinstance(dtype, pl.Datetime):
        return expr
    tz = dtype.time_zone
    if settings.normalize_tz:
        if tz is None:
            return expr.dt.replace_time_zone(settings.timezone)
        return expr.dt.convert_time_zone(settings.timezone)
    if tz is None:
        return expr
    return expr.dt.replace_time_zone(None)


def get_operator(name: str) -> Callable[[pl.Expr, Any], pl.Expr]:
    op = FilterHandler.OPERATORS.get(name)
    if not op:
        raise ValueError(f"Unsupported filter operator: {name}")
    return op
