from collections.abc import Callable
from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class ExportFormat:
    extension: str
    content_type: str
    writer: Callable[[pl.DataFrame, str], None]


EXPORT_FORMATS: dict[str, ExportFormat] = {
    'csv': ExportFormat('.csv', 'text/csv', lambda df, path: df.write_csv(path)),
    'parquet': ExportFormat('.parquet', 'application/octet-stream', lambda df, path: df.write_parquet(path)),
    'json': ExportFormat('.json', 'application/json', lambda df, path: df.write_json(path)),
    'ndjson': ExportFormat('.ndjson', 'application/x-ndjson', lambda df, path: df.write_ndjson(path)),
}


def get_export_format(name: str) -> ExportFormat:
    fmt = EXPORT_FORMATS.get(name)
    if not fmt:
        raise ValueError(f'Unsupported export format: {name}')
    return fmt
