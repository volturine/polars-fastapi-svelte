import logging
import os
import tempfile
import threading
import time

import duckdb
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import (
    DataSourceNotFoundError,
    EngineTimeoutError,
    JobNotFoundError,
    PipelineExecutionError,
    StepNotFoundError,
    UnsupportedExportFormatError,
)
from modules.compute.manager import get_manager
from modules.compute.schemas import ComputeResultSchema, ComputeStatusSchema, JobStatus
from modules.datasource.models import DataSource

logger = logging.getLogger(__name__)

# Job tracking (simple in-memory storage)
_job_results: dict[str, dict] = {}
_job_status: dict[str, dict] = {}
_job_lock = threading.Lock()


def cleanup_jobs_for_engine(analysis_id: str) -> int:
    """Clean up all jobs associated with an engine. Returns count of cleaned jobs."""
    with _job_lock:
        cleaned = 0
        for job_id in list(_job_status.keys()):
            if _job_status[job_id].get('analysis_id') == analysis_id:
                _job_status.pop(job_id, None)
                _job_results.pop(job_id, None)
                cleaned += 1
                logger.debug(f'Cleaned up job {job_id} for engine {analysis_id}')
        return cleaned


async def _get_additional_datasources(session: AsyncSession, pipeline_steps: list[dict]) -> dict[str, dict]:
    """Extract and fetch additional datasources referenced in pipeline steps (e.g., for joins)."""
    additional: dict[str, dict] = {}

    for step in pipeline_steps:
        config = step.get('config', {})
        right_source_id = config.get('right_source') or config.get('rightDataSource')

        union_sources = config.get('sources', [])
        if isinstance(union_sources, str):
            union_sources = [union_sources]

        if right_source_id and right_source_id not in additional:
            result = await session.execute(select(DataSource).where(DataSource.id == right_source_id))
            datasource = result.scalar_one_or_none()
            if datasource:
                additional[right_source_id] = {
                    'source_type': datasource.source_type,
                    **datasource.config,
                }

        for source_id in union_sources:
            if source_id in additional:
                continue
            result = await session.execute(select(DataSource).where(DataSource.id == source_id))
            datasource = result.scalar_one_or_none()
            if datasource:
                additional[source_id] = {
                    'source_type': datasource.source_type,
                    **datasource.config,
                }

    return additional


async def execute_analysis(
    session: AsyncSession,
    analysis_id: str,
    datasource_id: str,
    pipeline_steps: list[dict],
) -> ComputeStatusSchema:
    """
    Execute a data analysis pipeline asynchronously.

    Note: This function uses the preview command internally, which is efficient
    for most use cases. For full data export, use export_data() instead.

    Args:
        session: Database session
        analysis_id: Unique identifier for the analysis
        datasource_id: ID of the datasource to analyze
        pipeline_steps: List of pipeline step configurations

    Returns:
        ComputeStatusSchema with job status and metadata

    Raises:
        DataSourceNotFoundError: If datasource doesn't exist
        PipelineExecutionError: If pipeline execution fails
    """
    result = await session.execute(select(DataSource).where(DataSource.id == datasource_id))
    datasource = result.scalar_one_or_none()

    if not datasource:
        raise DataSourceNotFoundError(datasource_id)

    manager = get_manager()
    engine = manager.get_or_create_engine(analysis_id)

    datasource_config = {
        'source_type': datasource.source_type,
        **datasource.config,
    }

    additional_datasources = await _get_additional_datasources(session, pipeline_steps)

    # Use preview command with a reasonable row limit for async execution
    # For full data, use export_data() instead
    job_id = engine.preview(
        datasource_config=datasource_config,
        pipeline_steps=pipeline_steps,
        row_limit=10000,  # Default preview limit for async execution
        offset=0,
        additional_datasources=additional_datasources,
    )

    with _job_lock:
        _job_status[job_id] = {
            'job_id': job_id,
            'analysis_id': analysis_id,
            'status': JobStatus.PENDING,
            'progress': 0.0,
            'current_step': None,
            'error_message': None,
            'process_id': engine.process.pid if engine.process else None,
        }

    logger.info(f'Started job {job_id} for analysis {analysis_id}')
    return ComputeStatusSchema.model_validate(_job_status[job_id])


async def preview_step(
    session: AsyncSession,
    datasource_id: str,
    pipeline_steps: list[dict],
    target_step_id: str,
    row_limit: int = 1000,
    page: int = 1,
    timeout: int | None = None,
    analysis_id: str | None = None,
):
    """Preview the result of executing pipeline up to a specific step with pagination."""
    from modules.compute.schemas import StepPreviewResponse

    if timeout is None:
        timeout = settings.job_timeout

    if not analysis_id:
        # Create a temporary analysis_id for datasource preview
        analysis_id = f'__preview__{datasource_id}'

    result = await session.execute(select(DataSource).where(DataSource.id == datasource_id))
    datasource = result.scalar_one_or_none()

    if not datasource:
        raise DataSourceNotFoundError(datasource_id)

    # Find the step index by step_id
    step_index = None
    for idx, step in enumerate(pipeline_steps):
        if step.get('id') == target_step_id:
            step_index = idx
            break

    # Special case: previewing raw datasource (no pipeline steps, target is "source")
    if target_step_id == 'source' and len(pipeline_steps) == 0:
        preview_steps = []
    elif step_index is None:
        raise StepNotFoundError(target_step_id)
    else:
        preview_steps = pipeline_steps[: step_index + 1]

    manager = get_manager()
    engine = manager.get_engine(analysis_id)
    if not engine:
        engine = manager.get_or_create_engine(analysis_id)

    datasource_config = {
        'source_type': datasource.source_type,
        **datasource.config,
    }

    additional_datasources = await _get_additional_datasources(session, preview_steps)

    # Calculate offset for pagination
    offset = (page - 1) * row_limit

    # Use the new preview method that efficiently fetches only needed rows
    engine.preview(
        datasource_config=datasource_config,
        pipeline_steps=preview_steps,
        row_limit=row_limit,
        offset=offset,
        additional_datasources=additional_datasources,
    )

    start_time = time.time()
    while True:
        # Check timeout
        if time.time() - start_time > timeout:
            raise EngineTimeoutError(f'Preview operation timed out after {timeout} seconds', timeout)

        result_data = engine.get_result(timeout=1.0)
        if result_data:
            if result_data['status'] == JobStatus.COMPLETED:
                data = result_data['data'].get('data', [])
                schema = result_data['data'].get('schema', {})
                row_count = result_data['data'].get('row_count', 0)

                return StepPreviewResponse(
                    step_id=target_step_id,
                    columns=list(schema.keys()),
                    column_types=schema,
                    data=data,
                    total_rows=row_count,
                    page=page,
                    page_size=len(data),
                )
            elif result_data['status'] == JobStatus.FAILED:
                raise PipelineExecutionError(
                    f'Preview failed: {result_data.get("error", "Unknown error")}',
                    details={'operation': 'preview', 'datasource_id': datasource_id},
                )


def get_job_status(job_id: str) -> ComputeStatusSchema:
    """
    Get the current status of a compute job.

    This function polls the engine for updates and refreshes the cached status.

    Args:
        job_id: Unique identifier for the job

    Returns:
        ComputeStatusSchema with current job status

    Raises:
        JobNotFoundError: If job doesn't exist or has been cleaned up
    """
    # Poll engine for job status update
    manager = get_manager()

    for analysis_id in manager.list_engines():
        engine = manager.get_engine(analysis_id)
        if engine and engine.current_job_id == job_id:
            result = engine.get_result(timeout=0.1)
            if result:
                with _job_lock:
                    _job_status[job_id] = result
                    if result.get('data'):
                        _job_results[job_id] = result

    with _job_lock:
        if job_id not in _job_status:
            raise JobNotFoundError(job_id)
        status_data = _job_status[job_id]

    return ComputeStatusSchema.model_validate(status_data)


def get_job_result(job_id: str) -> ComputeResultSchema:
    """Get the result of a completed job."""
    with _job_lock:
        if job_id not in _job_results:
            raise JobNotFoundError(job_id)
        result = _job_results[job_id]

    return ComputeResultSchema(
        job_id=job_id,
        status=result['status'],
        data=result.get('data'),
        error=result.get('error'),
    )


def cancel_job(job_id: str) -> None:
    """Cancel a running job."""
    manager = get_manager()

    for analysis_id in manager.list_engines():
        engine = manager.get_engine(analysis_id)
        if engine and engine.current_job_id == job_id:
            manager.shutdown_engine(analysis_id)
            with _job_lock:
                _job_status[job_id] = {
                    'job_id': job_id,
                    'status': JobStatus.CANCELLED,
                    'progress': 0.0,
                    'current_step': None,
                    'error_message': 'Job cancelled by user',
                    'process_id': None,
                }
            return

    raise JobNotFoundError(job_id)


def cleanup_job(job_id: str) -> None:
    """Clean up job data from memory."""
    with _job_lock:
        _job_status.pop(job_id, None)
        _job_results.pop(job_id, None)
    logger.debug(f'Cleaned up job {job_id}')


async def get_step_schema(
    session: AsyncSession,
    datasource_id: str,
    pipeline_steps: list[dict],
    target_step_id: str,
    analysis_id: str,
    timeout: int | None = None,
):
    """Get the output schema of a pipeline step without returning data."""
    from modules.compute.schemas import StepSchemaResponse

    if timeout is None:
        timeout = settings.job_timeout

    result = await session.execute(select(DataSource).where(DataSource.id == datasource_id))
    datasource = result.scalar_one_or_none()

    if not datasource:
        raise DataSourceNotFoundError(datasource_id)

    # Find the step index by step_id
    step_index = None
    for idx, step in enumerate(pipeline_steps):
        if step.get('id') == target_step_id:
            step_index = idx
            break

    if step_index is None:
        raise StepNotFoundError(target_step_id)

    schema_steps = pipeline_steps[: step_index + 1]

    manager = get_manager()
    engine = manager.get_engine(analysis_id)
    if not engine:
        engine = manager.get_or_create_engine(analysis_id)

    datasource_config = {
        'source_type': datasource.source_type,
        **datasource.config,
    }

    additional_datasources = await _get_additional_datasources(session, schema_steps)

    # Use the new schema command that doesn't collect full data
    engine.get_schema(
        datasource_config=datasource_config,
        pipeline_steps=schema_steps,
        additional_datasources=additional_datasources,
    )

    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise EngineTimeoutError(f'Schema operation timed out after {timeout} seconds', timeout)

        result_data = engine.get_result(timeout=1.0)
        if result_data:
            if result_data['status'] == JobStatus.COMPLETED:
                schema = result_data['data'].get('schema', {})
                return StepSchemaResponse(
                    step_id=target_step_id,
                    columns=list(schema.keys()),
                    column_types=schema,
                )
            elif result_data['status'] == JobStatus.FAILED:
                raise PipelineExecutionError(
                    f'Schema fetch failed: {result_data.get("error", "Unknown error")}',
                    details={'operation': 'schema', 'datasource_id': datasource_id},
                )


async def export_data(
    session: AsyncSession,
    datasource_id: str,
    pipeline_steps: list[dict],
    target_step_id: str,
    export_format: str = 'csv',
    filename: str = 'export',
    destination: str = 'download',
    timeout: int | None = None,
    analysis_id: str | None = None,
) -> tuple[bytes, str, str]:
    """
    Export pipeline result to file.
    Returns (file_bytes, filename_with_ext, content_type).

    The engine subprocess writes the full dataset to a temp file,
    then we read it and return the bytes.
    """
    if timeout is None:
        timeout = settings.job_timeout

    result = await session.execute(select(DataSource).where(DataSource.id == datasource_id))
    datasource = result.scalar_one_or_none()

    if not datasource:
        raise DataSourceNotFoundError(datasource_id)

    # Find steps up to target
    step_index = None
    for idx, step in enumerate(pipeline_steps):
        if step.get('id') == target_step_id:
            step_index = idx
            break

    if step_index is None:
        raise StepNotFoundError(target_step_id)

    export_steps = pipeline_steps[: step_index + 1]

    manager = get_manager()

    # Use analysis engine if provided and exists, otherwise create temporary one
    temp_engine = False
    temp_engine_id = f'{datasource_id}_export'
    if analysis_id:
        engine = manager.get_engine(analysis_id)
        if not engine:
            engine = manager.get_or_create_engine(analysis_id)
    else:
        engine = manager.get_or_create_engine(temp_engine_id)
        temp_engine = True

    datasource_config = {
        'source_type': datasource.source_type,
        **datasource.config,
    }

    additional_datasources = await _get_additional_datasources(session, export_steps)

    # Determine file extension and content type
    format_config = {
        'csv': ('.csv', 'text/csv'),
        'parquet': ('.parquet', 'application/octet-stream'),
        'json': ('.json', 'application/json'),
        'ndjson': ('.ndjson', 'application/x-ndjson'),
        'duckdb': ('.parquet', 'application/octet-stream'),  # Export as parquet first
    }

    if export_format not in format_config:
        raise UnsupportedExportFormatError(export_format)

    ext, content_type = format_config[export_format]

    # For duckdb, we first export to parquet then convert
    actual_format = 'parquet' if export_format == 'duckdb' else export_format

    # Create temp file for engine to write to
    tmp_output = tempfile.mktemp(suffix=ext)

    try:
        # Use the new export method that writes full data directly to file
        engine.export(
            datasource_config=datasource_config,
            pipeline_steps=export_steps,
            output_path=tmp_output,
            export_format=actual_format,
            additional_datasources=additional_datasources,
        )

        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                if temp_engine:
                    manager.shutdown_engine(temp_engine_id)
                raise EngineTimeoutError(f'Export operation timed out after {timeout} seconds', timeout)

            result_data = engine.get_result(timeout=1.0)
            if result_data:
                if result_data['status'] == JobStatus.COMPLETED:
                    if temp_engine:
                        manager.shutdown_engine(temp_engine_id)

                    row_count = result_data['data'].get('row_count', 0)
                    logger.info(f'Export completed: {row_count} rows written to {export_format}')

                    # Handle DuckDB conversion
                    if export_format == 'duckdb':
                        tmp_db_path = tempfile.mktemp(suffix='.duckdb')
                        try:
                            conn = duckdb.connect(tmp_db_path)
                            conn.execute('CREATE TABLE data AS SELECT * FROM read_parquet(?)', [tmp_output])
                            conn.close()

                            with open(tmp_db_path, 'rb') as f:
                                file_bytes = f.read()

                            return file_bytes, f'{filename}.duckdb', 'application/octet-stream'
                        finally:
                            if os.path.exists(tmp_db_path):
                                os.unlink(tmp_db_path)

                    # Read the exported file
                    with open(tmp_output, 'rb') as f:
                        file_bytes = f.read()

                    return file_bytes, f'{filename}{ext}', content_type

                elif result_data['status'] == JobStatus.FAILED:
                    if temp_engine:
                        manager.shutdown_engine(temp_engine_id)
                    raise PipelineExecutionError(
                        f'Export failed: {result_data.get("error", "Unknown error")}',
                        details={'operation': 'export', 'datasource_id': datasource_id, 'export_format': export_format},
                    )
    finally:
        # Clean up temp file
        if os.path.exists(tmp_output):
            os.unlink(tmp_output)
