from enum import StrEnum


class StringTransformMethod(StrEnum):
    UPPERCASE = 'uppercase'
    LOWERCASE = 'lowercase'
    TITLE = 'title'
    STRIP = 'strip'
    LSTRIP = 'lstrip'
    RSTRIP = 'rstrip'
    LENGTH = 'length'
    SLICE = 'slice'
    REPLACE = 'replace'
    EXTRACT = 'extract'
    SPLIT = 'split'
    SPLIT_TAKE = 'split_take'


class TimeseriesOperationType(StrEnum):
    EXTRACT = 'extract'
    TIMESTAMP = 'timestamp'
    ADD = 'add'
    SUBTRACT = 'subtract'
    OFFSET = 'offset'
    DIFF = 'diff'
    TRUNCATE = 'truncate'
    ROUND = 'round'


class TimeComponent(StrEnum):
    YEAR = 'year'
    MONTH = 'month'
    DAY = 'day'
    HOUR = 'hour'
    MINUTE = 'minute'
    SECOND = 'second'
    QUARTER = 'quarter'
    WEEK = 'week'
    DAYOFWEEK = 'dayofweek'


class DurationUnit(StrEnum):
    SECONDS = 'seconds'
    MINUTES = 'minutes'
    HOURS = 'hours'
    DAYS = 'days'
    WEEKS = 'weeks'
    MONTHS = 'months'


class TimeDirection(StrEnum):
    ADD = 'add'
    SUBTRACT = 'subtract'


class WithColumnsExprType(StrEnum):
    LITERAL = 'literal'
    COLUMN = 'column'
    UDF = 'udf'
