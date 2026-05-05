from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl
import pytest
from modules.datasource.source_types import DataSourceType
from sqlmodel import Session

from contracts.datasource.models import DataSource


def _clean_dir() -> Path:
    from core.namespace import namespace_paths

    return namespace_paths().clean_dir


def _read_dataframe(datasource: DataSource) -> pl.DataFrame:
    config = datasource.config if isinstance(datasource.config, dict) else {}
    source = config.get('source') if datasource.source_type == DataSourceType.ICEBERG else config
    if not isinstance(source, dict):
        source = config
    file_path = source.get('file_path')
    file_type = source.get('file_type')
    if not isinstance(file_path, str):
        return pl.DataFrame()
    if file_type == 'parquet':
        return pl.read_parquet(file_path)
    if file_type == 'json':
        return pl.read_json(file_path)
    if file_type == 'ndjson':
        return pl.read_ndjson(file_path)
    if file_type == 'excel':
        return pl.read_excel(file_path)
    return pl.read_csv(file_path)


def _schema_for(datasource: DataSource):
    from modules.datasource import schemas

    df = _read_dataframe(datasource)
    return schemas.SchemaInfo(
        columns=[
            schemas.ColumnSchema(
                name=name,
                dtype=str(dtype),
                nullable=True,
                sample_value=None if df.height == 0 else str(df[name][0]),
            )
            for name, dtype in zip(df.columns, df.dtypes, strict=True)
        ],
        row_count=df.height,
    )


def _response(datasource: DataSource):
    from modules.datasource import schemas

    response = schemas.DataSourceResponse.model_validate(datasource)
    response.output_of_tab_id = datasource.config.get('analysis_tab_id') if isinstance(datasource.config, dict) else None
    return response


async def _fake_create_file_datasource(
    session: Session,
    *,
    name: str,
    description: str | None,
    file_path: str,
    file_type: str,
    options: dict[str, Any] | None = None,
    csv_options: dict[str, object] | None = None,
    owner_id: str | None = None,
    **kwargs: Any,
):
    datasource = DataSource(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        source_type=DataSourceType.ICEBERG,
        config={
            'metadata_path': str(_clean_dir() / uuid.uuid4().hex / 'master'),
            'branch': 'master',
            'source': {
                'source_type': 'file',
                'file_path': file_path,
                'file_type': file_type,
                'options': options or csv_options or {},
                **{key: value for key, value in kwargs.items() if value is not None and key not in {'runtime_probe', 'branch'}},
            },
        },
        owner_id=owner_id,
        created_by='import',
        created_at=datetime.now(UTC),
    )
    datasource.schema_cache = _schema_for(datasource).model_dump(exclude_none=True)
    Path(datasource.config['metadata_path']).mkdir(parents=True, exist_ok=True)
    session.add(datasource)
    session.commit()
    session.refresh(datasource)
    return _response(datasource)


async def _fake_create_database_datasource(
    session: Session,
    *,
    name: str,
    description: str | None,
    connection_string: str,
    query: str,
    branch: str,
    owner_id: str | None = None,
    **kwargs: Any,
):
    del kwargs
    datasource = DataSource(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        source_type=DataSourceType.DATABASE,
        config={'connection_string': connection_string, 'query': query, 'branch': branch},
        owner_id=owner_id,
        created_by='import',
        created_at=datetime.now(UTC),
    )
    session.add(datasource)
    session.commit()
    session.refresh(datasource)
    return _response(datasource)


async def _fake_create_iceberg_datasource(
    session: Session,
    *,
    name: str,
    description: str | None,
    source: dict[str, object],
    branch: str,
    owner_id: str | None = None,
    **kwargs: Any,
):
    return await _fake_create_file_datasource(
        session,
        name=name,
        description=description,
        file_path=str(source.get('file_path')),
        file_type=str(source.get('file_type', 'csv')),
        options=source.get('options') if isinstance(source.get('options'), dict) else {},
        owner_id=owner_id,
        branch=branch,
        **kwargs,
    )


async def _fake_get_datasource_schema(session: Session, *, datasource_id: str, **kwargs: Any):
    del kwargs
    datasource = session.get(DataSource, datasource_id)
    if datasource is None:
        from core.exceptions import DataSourceNotFoundError

        raise DataSourceNotFoundError(datasource_id)
    schema = _schema_for(datasource)
    datasource.schema_cache = schema.model_dump(exclude_none=True)
    session.add(datasource)
    session.commit()
    return schema


async def _fake_refresh_datasource(session: Session, *, datasource_id: str, **kwargs: Any):
    del kwargs
    datasource = session.get(DataSource, datasource_id)
    if datasource is None:
        from core.exceptions import DataSourceNotFoundError

        raise DataSourceNotFoundError(datasource_id)
    datasource.schema_cache = _schema_for(datasource).model_dump(exclude_none=True)
    session.add(datasource)
    session.commit()
    session.refresh(datasource)
    return _response(datasource)


async def _fake_get_column_stats(session: Session, *, datasource_id: str, column_name: str, **kwargs: Any):
    del kwargs
    from modules.datasource import schemas

    datasource = session.get(DataSource, datasource_id)
    if datasource is None:
        from core.exceptions import DataSourceNotFoundError

        raise DataSourceNotFoundError(datasource_id)
    series = _read_dataframe(datasource)[column_name]
    count = len(series)
    null_count = series.null_count()
    return schemas.ColumnStatsResponse(
        column=column_name,
        dtype=str(series.dtype),
        count=count,
        null_count=null_count,
        null_percentage=(null_count / count * 100) if count else 0,
        unique=series.n_unique(),
        min=series.min(),
        max=series.max(),
    )


@pytest.fixture(autouse=True)
def fake_datasource_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    from modules.datasource import routes

    monkeypatch.setattr(routes, 'create_remote_file_datasource', _fake_create_file_datasource)
    monkeypatch.setattr(routes, 'create_remote_database_datasource', _fake_create_database_datasource)
    monkeypatch.setattr(routes, 'create_remote_iceberg_datasource', _fake_create_iceberg_datasource)
    monkeypatch.setattr(routes, 'get_remote_datasource_schema', _fake_get_datasource_schema)
    monkeypatch.setattr(routes, 'refresh_remote_datasource', _fake_refresh_datasource)
    monkeypatch.setattr(routes, 'get_remote_column_stats', _fake_get_column_stats)
