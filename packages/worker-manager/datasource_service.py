import logging
import os
import uuid
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl
import psycopg
from compute_operations.datasource import load_datasource
from datasource_schemas import ColumnSchema, CSVOptions, DataSourceResponse, SchemaInfo, normalize_datasource_description
from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table
from sqlmodel import Session

from contracts.datasource.models import DataSource
from contracts.datasource.source_types import FILE_BASED_CATEGORIES, SOURCE_TYPE_CATEGORY, DataSourceType
from core import engine_runs_service as engine_run_service
from core.config import settings
from core.exceptions import DataSourceConnectionError, DataSourceNotFoundError, DataSourceValidationError
from core.namespace import get_namespace, namespace_paths

logger = logging.getLogger(__name__)


def _prepare_clean_target(clean_dir: Path, datasource_id: str, branch: str) -> Path:
    target = clean_dir / datasource_id / branch
    target.mkdir(parents=True, exist_ok=True)
    return target


def _write_iceberg_table(lazy: pl.LazyFrame, table_path: Path, build_mode: str) -> Table:
    catalog = load_catalog(
        'local',
        type='sql',
        uri=settings.database_url,
        warehouse=f'file://{table_path.parent}',
    )
    namespace = 'clean'
    catalog.create_namespace_if_not_exists(namespace)
    identifier = f'{namespace}.{table_path.parent.name}'
    arrow_table = lazy.collect().to_arrow()
    if build_mode == 'recreate' and catalog.table_exists(identifier):
        catalog.drop_table(identifier)
    if catalog.table_exists(identifier):
        table = catalog.load_table(identifier)
        if build_mode == 'incremental':
            table.append(arrow_table)
        else:
            _sync_iceberg_schema(table, arrow_table.schema)
            table.overwrite(arrow_table)
        return table
    table = catalog.create_table(identifier, schema=arrow_table.schema, location=str(table_path))
    table.append(arrow_table)
    return table


def _build_iceberg_config(paths, target_path: Path, branch: str, source_config: Mapping[str, object] | None = None) -> dict[str, object]:
    return {
        'catalog_type': 'sql',
        'catalog_uri': settings.database_url,
        'warehouse': f'file://{paths.clean_dir}',
        'namespace': 'clean',
        'table': target_path.parent.name,
        'metadata_path': str(target_path.parent),
        'branch': branch,
        'source': dict(source_config) if source_config is not None else None,
        'namespace_name': get_namespace(),
        'refresh': None,
    }


def _sync_iceberg_schema(table: Table, new_schema: Any) -> None:
    from iceberg_reader import sync_iceberg_schema

    sync_iceberg_schema(table, new_schema)


def _set_snapshot_metadata(config: dict[str, object], snapshot: Any | None) -> None:
    if snapshot is None:
        return
    config['current_snapshot_id'] = str(snapshot.snapshot_id)
    config['current_snapshot_timestamp_ms'] = int(snapshot.timestamp_ms)
    config['snapshot_id'] = str(snapshot.snapshot_id)
    config['snapshot_timestamp_ms'] = int(snapshot.timestamp_ms)


def _schema_cache_payload(schema_info: SchemaInfo) -> dict[str, Any]:
    columns = [column.model_dump(exclude={'description'}) for column in schema_info.columns]
    return schema_info.model_dump(exclude={'columns'}) | {'columns': columns}


def _get_first_non_null_samples(lazy: pl.LazyFrame, max_rows: int = 1000) -> dict[str, str | None]:
    columns = lazy.collect_schema().names()
    exprs = [pl.col(column).drop_nulls().first().alias(column) for column in columns]
    result = lazy.head(max_rows).select(exprs).collect()
    if result.height == 0:
        return dict.fromkeys(columns)
    return {column: (str(result[column][0]) if result[column][0] is not None else None) for column in columns}


def _schema_from_analysis(datasource: DataSource, sheet_name: str | None) -> SchemaInfo:
    del sheet_name
    raise DataSourceValidationError(
        'Schema extraction not supported for analysis datasources',
        details={'datasource_id': datasource.id},
    )


def _schema_from_database(datasource: DataSource, sheet_name: str | None) -> SchemaInfo:
    del sheet_name
    connection_string = datasource.config['connection_string']
    query = datasource.config['query']
    if not connection_string.lower().startswith('postgresql://'):
        raise DataSourceConnectionError('Database datasource connection string must be PostgreSQL')
    try:
        with psycopg.connect(connection_string, autocommit=True) as connection:
            frame = pl.read_database(query, connection)
    except Exception as exc:
        raise DataSourceConnectionError(
            'Failed to query database datasource',
            details={'datasource_id': datasource.id, 'source_type': datasource.source_type},
        ) from exc
    sample_values = _get_first_non_null_samples(frame.lazy())
    columns = [
        ColumnSchema(name=name, dtype=str(dtype), nullable=True, sample_value=sample_values.get(name))
        for name, dtype in frame.schema.items()
    ]
    return SchemaInfo(columns=columns, row_count=frame.height)


def _schema_from_file(datasource: DataSource, sheet_name: str | None) -> SchemaInfo:
    config = {'source_type': datasource.source_type, **datasource.config}
    if sheet_name:
        config = {**config, 'sheet_name': sheet_name}
    try:
        lazy = load_datasource(config)
    except Exception as exc:
        category = SOURCE_TYPE_CATEGORY.get(DataSourceType(datasource.source_type))
        label = category.value if category else 'datasource'
        raise DataSourceConnectionError(
            f'Failed to load {label} datasource',
            details={'datasource_id': datasource.id, 'source_type': datasource.source_type},
        ) from exc
    sample_values = _get_first_non_null_samples(lazy)
    columns = [
        ColumnSchema(name=name, dtype=str(dtype), nullable=True, sample_value=sample_values.get(name))
        for name, dtype in lazy.collect_schema().items()
    ]
    return SchemaInfo(columns=columns, row_count=lazy.select(pl.len()).collect().item())


_SCHEMA_HANDLERS: dict[DataSourceType, Callable[[DataSource, str | None], SchemaInfo]] = {
    DataSourceType.ANALYSIS: _schema_from_analysis,
    DataSourceType.DATABASE: _schema_from_database,
    **{
        source_type: _schema_from_file
        for source_type in SOURCE_TYPE_CATEGORY
        if SOURCE_TYPE_CATEGORY[source_type] in FILE_BASED_CATEGORIES
        and source_type not in {DataSourceType.ANALYSIS, DataSourceType.DATABASE}
    },
}


def _extract_schema(datasource: DataSource, sheet_name: str | None = None) -> SchemaInfo:
    try:
        source_type = DataSourceType(datasource.source_type)
    except ValueError as exc:
        raise DataSourceConnectionError(
            'Unsupported datasource type for schema extraction',
            details={'datasource_id': datasource.id, 'source_type': datasource.source_type},
        ) from exc
    handler = _SCHEMA_HANDLERS.get(source_type)
    if handler is None:
        raise DataSourceConnectionError(
            'Unsupported datasource type for schema extraction',
            details={'datasource_id': datasource.id, 'source_type': datasource.source_type},
        )
    return handler(datasource, sheet_name)


def _build_datasource_result_json(
    datasource_id: str,
    name: str,
    source_type: DataSourceType,
    config: Mapping[str, object],
) -> dict[str, str]:
    result = {'datasource_id': datasource_id, 'datasource_name': name}
    if source_type != DataSourceType.ICEBERG:
        return result
    source = config.get('source')
    if not isinstance(source, dict):
        return result
    source_type_value = source.get('source_type')
    if source_type_value not in {DataSourceType.FILE, DataSourceType.FILE.value, DataSourceType.DATABASE, DataSourceType.DATABASE.value}:
        return result
    snapshot_id = config.get('current_snapshot_id')
    if snapshot_id is None:
        snapshot_id = config.get('snapshot_id')
    if snapshot_id is None:
        return result
    result['snapshot_id'] = str(snapshot_id)
    return result


def _log_datasource_create(
    session: Session,
    datasource_id: str,
    name: str,
    source_type: DataSourceType,
    config: Mapping[str, object],
    branch: str,
) -> None:
    payload = engine_run_service.create_engine_run_payload(
        analysis_id=None,
        datasource_id=datasource_id,
        kind='datasource_create',
        status='success',
        request_json={
            'name': name,
            'source_type': source_type.value,
            'config': config,
            'iceberg_options': {'branch': branch},
        },
        result_json=_build_datasource_result_json(datasource_id, name, source_type, config),
    )
    engine_run_service.create_engine_run(session, payload)


def _log_datasource_update(
    session: Session,
    datasource_id: str,
    name: str,
    config: Mapping[str, object],
    branch: str | None,
) -> None:
    request_json: dict[str, object] = {'name': name, 'source_type': DataSourceType.ICEBERG.value, 'config': dict(config)}
    if branch is not None:
        request_json['iceberg_options'] = {'branch': branch}
    payload = engine_run_service.create_engine_run_payload(
        analysis_id=None,
        datasource_id=datasource_id,
        kind='datasource_update',
        status='success',
        request_json=request_json,
        result_json=_build_datasource_result_json(datasource_id, name, DataSourceType.ICEBERG, config),
    )
    engine_run_service.create_engine_run(session, payload)


def _persist_schema_cache(session: Session, datasource: DataSource) -> None:
    schema_info = _extract_schema(datasource)
    datasource.schema_cache = _schema_cache_payload(schema_info)
    session.add(datasource)
    session.commit()
    session.refresh(datasource)


def create_file_datasource(
    session: Session,
    name: str,
    description: str | None,
    file_path: str,
    file_type: str,
    options: dict | None = None,
    csv_options: CSVOptions | None = None,
    sheet_name: str | None = None,
    start_row: int | None = None,
    start_col: int | None = None,
    end_col: int | None = None,
    end_row: int | None = None,
    has_header: bool | None = None,
    table_name: str | None = None,
    named_range: str | None = None,
    cell_range: str | None = None,
    owner_id: str | None = None,
) -> DataSourceResponse:
    datasource_id = str(uuid.uuid4())
    resolved_path = Path(os.path.realpath(Path(file_path).resolve()))
    paths = namespace_paths()
    data_root = Path(os.path.realpath(paths.base_dir.resolve()))
    upload_root = Path(os.path.realpath(paths.upload_dir.resolve()))
    within_data_root = data_root in resolved_path.parents or data_root == resolved_path
    within_upload_root = upload_root in resolved_path.parents or upload_root == resolved_path
    if not (within_data_root or within_upload_root):
        raise ValueError(f'Path must be inside data directory: {data_root}')
    if file_type in {'csv', 'json', 'ndjson', 'excel'} and not resolved_path.is_file():
        raise ValueError(f'Path must be a file for type: {file_type}')
    if file_type == 'parquet' and not (resolved_path.is_file() or resolved_path.is_dir()):
        raise ValueError('Parquet path must be a file or directory')

    source_config = {
        'source_type': DataSourceType.FILE,
        'file_path': str(resolved_path),
        'file_type': file_type,
        'options': options or {},
        'csv_options': csv_options.model_dump() if csv_options else None,
        'sheet_name': sheet_name,
        'start_row': start_row,
        'start_col': start_col,
        'end_col': end_col,
        'end_row': end_row,
        'has_header': has_header,
        'table_name': table_name,
        'named_range': named_range,
        'cell_range': cell_range,
    }
    try:
        lazy = load_datasource(source_config)
    except Exception as exc:
        raise DataSourceValidationError(
            f'Failed to load file datasource for ingestion: {exc}',
            details={'file_path': str(resolved_path), 'file_type': file_type},
        ) from exc
    target_path = _prepare_clean_target(paths.clean_dir, datasource_id, 'master')
    snapshot = _write_iceberg_table(lazy, target_path, build_mode='recreate')
    config = _build_iceberg_config(paths, target_path, branch='master', source_config=source_config)
    _set_snapshot_metadata(config, snapshot.current_snapshot() if snapshot else None)
    datasource = DataSource(
        id=datasource_id,
        name=name,
        description=normalize_datasource_description(description),
        source_type=DataSourceType.ICEBERG,
        config=config,
        owner_id=owner_id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    session.add(datasource)
    session.commit()
    session.refresh(datasource)
    _log_datasource_create(session, datasource_id, name, DataSourceType.ICEBERG, config, branch='master')
    try:
        _persist_schema_cache(session, datasource)
    except Exception as exc:
        session.rollback()
        raise DataSourceValidationError(
            f'Failed to extract schema for datasource {datasource_id}: {exc}',
            details={'datasource_id': datasource_id},
        ) from exc
    return DataSourceResponse.model_validate(datasource)


def create_database_datasource(
    session: Session,
    name: str,
    description: str | None,
    connection_string: str,
    query: str,
    branch: str = 'master',
    owner_id: str | None = None,
) -> DataSourceResponse:
    datasource_id = str(uuid.uuid4())
    source_config = {'connection_string': connection_string, 'query': query, 'branch': branch}
    try:
        lazy = load_datasource(
            {'source_type': DataSourceType.DATABASE, 'connection_string': connection_string, 'query': query},
        )
    except Exception as exc:
        if connection_string.startswith('postgresql://'):
            datasource = DataSource(
                id=datasource_id,
                name=name,
                description=normalize_datasource_description(description),
                source_type=DataSourceType.DATABASE,
                config=source_config,
                owner_id=owner_id,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            )
            session.add(datasource)
            session.commit()
            session.refresh(datasource)
            _log_datasource_create(session, datasource_id, name, DataSourceType.DATABASE, source_config, branch=branch)
            return DataSourceResponse.model_validate(datasource)
        raise DataSourceConnectionError(
            'Failed to query database datasource',
            details={'connection_string': connection_string},
        ) from exc
    paths = namespace_paths()
    target_path = _prepare_clean_target(paths.clean_dir, datasource_id, branch)
    snapshot = _write_iceberg_table(lazy, target_path, build_mode='recreate')
    config = _build_iceberg_config(paths, target_path, branch=branch, source_config=source_config)
    _set_snapshot_metadata(config, snapshot.current_snapshot() if snapshot else None)
    datasource = DataSource(
        id=datasource_id,
        name=name,
        description=normalize_datasource_description(description),
        source_type=DataSourceType.ICEBERG,
        config=config,
        owner_id=owner_id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    session.add(datasource)
    session.commit()
    session.refresh(datasource)
    _log_datasource_create(session, datasource_id, name, DataSourceType.ICEBERG, config, branch=branch)
    try:
        _persist_schema_cache(session, datasource)
    except Exception as exc:
        session.rollback()
        raise DataSourceValidationError(
            f'Failed to extract schema for datasource {datasource_id}: {exc}',
            details={'datasource_id': datasource_id},
        ) from exc
    return DataSourceResponse.model_validate(datasource)


def create_iceberg_datasource(
    session: Session,
    name: str,
    description: str | None,
    source: dict,
    branch: str = 'master',
    owner_id: str | None = None,
) -> DataSourceResponse:
    source_type = source.get('source_type') if isinstance(source, dict) else None
    if source_type not in {DataSourceType.FILE, DataSourceType.DATABASE}:
        raise DataSourceValidationError(
            'Iceberg datasource source_type is not supported for ingestion',
            details={'source_type': source_type},
        )
    if not isinstance(branch, str) or not branch.strip():
        raise DataSourceValidationError('Branch is required', details={'source_type': source_type})
    branch_name = branch.strip()
    try:
        if source_type == DataSourceType.DATABASE:
            connection_string = source.get('connection_string')
            query = source.get('query')
            if not connection_string or not query:
                raise DataSourceValidationError(
                    'Datasource source is missing connection details',
                    details={'source_type': source_type},
                )
            lazy = load_datasource(
                {'source_type': DataSourceType.DATABASE, 'connection_string': connection_string, 'query': query},
            )
        else:
            lazy = load_datasource(source)
    except DataSourceValidationError:
        raise
    except Exception as exc:
        message = 'Failed to query database datasource' if source_type == DataSourceType.DATABASE else 'Failed to read file datasource'
        raise DataSourceConnectionError(message, details={'source_type': source_type}) from exc
    datasource_id = str(uuid.uuid4())
    paths = namespace_paths()
    target_path = _prepare_clean_target(paths.clean_dir, datasource_id, branch_name)
    snapshot = _write_iceberg_table(lazy, target_path, build_mode='recreate')
    config = _build_iceberg_config(paths, target_path, branch=branch_name, source_config=source)
    _set_snapshot_metadata(config, snapshot.current_snapshot() if snapshot else None)
    datasource = DataSource(
        id=datasource_id,
        name=name,
        description=normalize_datasource_description(description),
        source_type=DataSourceType.ICEBERG,
        config=config,
        owner_id=owner_id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    session.add(datasource)
    session.commit()
    session.refresh(datasource)
    _log_datasource_create(session, datasource_id, name, DataSourceType.ICEBERG, config, branch=branch_name)
    try:
        _persist_schema_cache(session, datasource)
    except Exception as exc:
        session.rollback()
        raise DataSourceValidationError(
            f'Failed to extract schema for datasource {datasource_id}: {exc}',
            details={'datasource_id': datasource_id},
        ) from exc
    return DataSourceResponse.model_validate(datasource)


def refresh_external_datasource(session: Session, datasource_id: str) -> DataSourceResponse:
    datasource = session.get(DataSource, datasource_id)
    if datasource is None:
        raise DataSourceNotFoundError(datasource_id)
    if datasource.source_type != DataSourceType.ICEBERG:
        raise DataSourceValidationError(
            'Refresh is only available for Iceberg datasources',
            details={'datasource_id': datasource_id},
        )
    source = datasource.config.get('source') if isinstance(datasource.config, dict) else None
    if not isinstance(source, dict):
        raise DataSourceValidationError(
            'Datasource has no external source configuration',
            details={'datasource_id': datasource_id},
        )
    source_type = source.get('source_type')
    if source_type not in {DataSourceType.DATABASE, DataSourceType.FILE}:
        raise DataSourceValidationError(
            'Datasource source is not refreshable',
            details={'datasource_id': datasource_id, 'source_type': source_type},
        )
    branch_raw = datasource.config.get('branch', source.get('branch'))
    if not isinstance(branch_raw, str) or not branch_raw.strip():
        raise DataSourceValidationError(
            'Datasource branch is required',
            details={'datasource_id': datasource_id},
        )
    try:
        if source_type == DataSourceType.DATABASE:
            connection_string = source.get('connection_string')
            query = source.get('query')
            if not connection_string or not query:
                raise DataSourceValidationError(
                    'Datasource source is missing connection details',
                    details={'datasource_id': datasource_id},
                )
            lazy = load_datasource(
                {'source_type': DataSourceType.DATABASE, 'connection_string': connection_string, 'query': query},
            )
        else:
            lazy = load_datasource(source)
    except DataSourceValidationError:
        raise
    except Exception as exc:
        message = 'Failed to query database datasource' if source_type == DataSourceType.DATABASE else 'Failed to read file datasource'
        raise DataSourceConnectionError(message, details={'datasource_id': datasource_id}) from exc
    metadata_path = datasource.config.get('metadata_path')
    if not isinstance(metadata_path, str) or not metadata_path:
        raise DataSourceValidationError(
            'Datasource missing metadata_path',
            details={'datasource_id': datasource_id},
        )
    branch = branch_raw.strip()
    target_path = Path(metadata_path)
    if target_path.name != branch:
        target_path = _prepare_clean_target(namespace_paths().clean_dir, datasource_id, branch)
    snapshot = _write_iceberg_table(lazy, target_path, build_mode='full')
    next_config = dict(datasource.config)
    _set_snapshot_metadata(next_config, snapshot.current_snapshot() if snapshot else None)
    next_config['branch'] = branch
    next_config['metadata_path'] = str(target_path)
    next_config['source'] = source
    next_config['refresh'] = {'refreshed_at': datetime.now(UTC).replace(tzinfo=None).isoformat()}
    datasource.config = next_config
    datasource.schema_cache = None
    session.add(datasource)
    session.commit()
    session.refresh(datasource)
    _log_datasource_update(session, datasource.id, datasource.name, next_config, branch=branch)
    return DataSourceResponse.model_validate(datasource)


def is_reingestable_raw_datasource(datasource: DataSource) -> bool:
    if datasource.source_type != DataSourceType.ICEBERG:
        return False
    if datasource.created_by == 'analysis':
        return False
    if not isinstance(datasource.config, dict):
        return False
    source = datasource.config.get('source')
    if not isinstance(source, dict):
        return False
    source_type = source.get('source_type')
    return source_type in {DataSourceType.FILE, DataSourceType.DATABASE}


def refresh_datasource_for_schedule(session: Session, datasource_id: str) -> DataSourceResponse:
    datasource = session.get(DataSource, datasource_id)
    if datasource is None:
        raise DataSourceNotFoundError(datasource_id)
    if is_reingestable_raw_datasource(datasource):
        return refresh_external_datasource(session, datasource_id)
    schema = _extract_schema(datasource)
    next_config = dict(datasource.config) if isinstance(datasource.config, dict) else {}
    next_config['refresh'] = {
        'refreshed_at': datetime.now(UTC).replace(tzinfo=None).isoformat(),
        'mode': 'schedule_schema_refresh',
    }
    datasource.config = next_config
    datasource.schema_cache = _schema_cache_payload(schema)
    session.add(datasource)
    session.commit()
    session.refresh(datasource)
    payload = engine_run_service.create_engine_run_payload(
        analysis_id=None,
        datasource_id=datasource.id,
        kind='datasource_update',
        status='success',
        request_json={
            'name': datasource.name,
            'source_type': datasource.source_type,
            'mode': 'schedule_schema_refresh',
            'config': datasource.config,
        },
        result_json={
            'datasource_id': datasource.id,
            'datasource_name': datasource.name,
            'schema_columns': len(schema.columns),
            'row_count': schema.row_count,
        },
        triggered_by='schedule',
    )
    engine_run_service.create_engine_run(session, payload)
    return DataSourceResponse.model_validate(datasource)
