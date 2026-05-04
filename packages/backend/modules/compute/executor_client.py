from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import HTTPException
from sqlmodel import Session

from contracts.compute import schemas as compute_schemas
from contracts.compute_requests.live import response_hub
from contracts.compute_requests.models import ComputeRequestKind, ComputeRequestStatus
from contracts.runtime import ipc as runtime_ipc
from contracts.runtime_workers.models import RuntimeWorkerKind
from core import compute_requests_service
from core.dependencies import RuntimeAvailabilityProbe
from core.exceptions import PipelineExecutionError
from core.namespace import get_namespace
from modules.datasource import schemas as datasource_schemas


def _ensure_runtime_available(runtime_probe: RuntimeAvailabilityProbe) -> None:
    if runtime_probe.available(kind=RuntimeWorkerKind.BUILD_MANAGER):
        return
    raise HTTPException(status_code=503, detail='Compute runtime unavailable')


async def _submit_and_wait(
    session: Session,
    *,
    kind: ComputeRequestKind,
    request_json: dict[str, object],
    runtime_probe: RuntimeAvailabilityProbe,
):
    _ensure_runtime_available(runtime_probe)
    request = compute_requests_service.create_request(
        session,
        namespace=get_namespace(),
        kind=kind,
        request_json=request_json,
    )
    wait_task = asyncio.create_task(response_hub.wait(request.id))
    await asyncio.to_thread(runtime_ipc.notify_compute_request, request.id)
    await asyncio.gather(wait_task)
    session.expire_all()
    completed = compute_requests_service.get_request(session, request.id)
    if completed is None:
        raise PipelineExecutionError(f'Compute request {request.id} disappeared')
    if completed.status == ComputeRequestStatus.COMPLETED:
        return completed
    payload = completed.response_json or {}
    message = str(payload.get('error') or completed.error_message or 'Compute request failed')
    status_code = payload.get('status_code')
    if isinstance(status_code, int):
        raise HTTPException(status_code=status_code, detail=message)
    raise PipelineExecutionError(message)


async def preview_step(
    session: Session,
    request: compute_schemas.StepPreviewRequest,
    *,
    runtime_probe: RuntimeAvailabilityProbe,
) -> compute_schemas.StepPreviewResponse:
    completed = await _submit_and_wait(
        session,
        kind=ComputeRequestKind.PREVIEW,
        request_json=request.model_dump(mode='json'),
        runtime_probe=runtime_probe,
    )
    return compute_schemas.StepPreviewResponse.model_validate(completed.response_json)


async def get_step_schema(
    session: Session,
    request: compute_schemas.StepSchemaRequest,
    *,
    runtime_probe: RuntimeAvailabilityProbe,
) -> compute_schemas.StepSchemaResponse:
    completed = await _submit_and_wait(
        session,
        kind=ComputeRequestKind.SCHEMA,
        request_json=request.model_dump(mode='json'),
        runtime_probe=runtime_probe,
    )
    return compute_schemas.StepSchemaResponse.model_validate(completed.response_json)


async def get_step_row_count(
    session: Session,
    request: compute_schemas.StepRowCountRequest,
    *,
    runtime_probe: RuntimeAvailabilityProbe,
) -> compute_schemas.StepRowCountResponse:
    completed = await _submit_and_wait(
        session,
        kind=ComputeRequestKind.ROW_COUNT,
        request_json=request.model_dump(mode='json'),
        runtime_probe=runtime_probe,
    )
    return compute_schemas.StepRowCountResponse.model_validate(completed.response_json)


async def download_step(
    session: Session,
    request: compute_schemas.DownloadRequest,
    *,
    runtime_probe: RuntimeAvailabilityProbe,
) -> tuple[bytes, str, str]:
    completed = await _submit_and_wait(
        session,
        kind=ComputeRequestKind.DOWNLOAD,
        request_json=request.model_dump(mode='json'),
        runtime_probe=runtime_probe,
    )
    if not completed.artifact_path or not completed.artifact_name or not completed.artifact_content_type:
        raise PipelineExecutionError('Download artifact missing from compute response')
    path = Path(completed.artifact_path)
    data = path.read_bytes()
    path.unlink(missing_ok=True)
    return data, completed.artifact_name, completed.artifact_content_type


async def export_data(
    session: Session,
    request: compute_schemas.ExportRequest,
    *,
    runtime_probe: RuntimeAvailabilityProbe,
) -> compute_schemas.ExportResponse:
    completed = await _submit_and_wait(
        session,
        kind=ComputeRequestKind.EXPORT,
        request_json=request.model_dump(mode='json'),
        runtime_probe=runtime_probe,
    )
    return compute_schemas.ExportResponse.model_validate(completed.response_json)


async def create_file_datasource(
    session: Session,
    *,
    runtime_probe: RuntimeAvailabilityProbe,
    name: str,
    description: str | None,
    file_path: str,
    file_type: str,
    options: dict | None = None,
    csv_options: dict[str, object] | None = None,
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
) -> datasource_schemas.DataSourceResponse:
    completed = await _submit_and_wait(
        session,
        kind=ComputeRequestKind.CREATE_FILE_DATASOURCE,
        runtime_probe=runtime_probe,
        request_json={
            'name': name,
            'description': description,
            'file_path': file_path,
            'file_type': file_type,
            'options': options or {},
            'csv_options': csv_options,
            'sheet_name': sheet_name,
            'start_row': start_row,
            'start_col': start_col,
            'end_col': end_col,
            'end_row': end_row,
            'has_header': has_header,
            'table_name': table_name,
            'named_range': named_range,
            'cell_range': cell_range,
            'owner_id': owner_id,
        },
    )
    return datasource_schemas.DataSourceResponse.model_validate(completed.response_json)


async def create_database_datasource(
    session: Session,
    *,
    runtime_probe: RuntimeAvailabilityProbe,
    name: str,
    description: str | None,
    connection_string: str,
    query: str,
    branch: str,
    owner_id: str | None = None,
) -> datasource_schemas.DataSourceResponse:
    completed = await _submit_and_wait(
        session,
        kind=ComputeRequestKind.CREATE_DATABASE_DATASOURCE,
        runtime_probe=runtime_probe,
        request_json={
            'name': name,
            'description': description,
            'connection_string': connection_string,
            'query': query,
            'branch': branch,
            'owner_id': owner_id,
        },
    )
    return datasource_schemas.DataSourceResponse.model_validate(completed.response_json)


async def create_iceberg_datasource(
    session: Session,
    *,
    runtime_probe: RuntimeAvailabilityProbe,
    name: str,
    description: str | None,
    source: dict[str, object],
    branch: str,
    owner_id: str | None = None,
) -> datasource_schemas.DataSourceResponse:
    completed = await _submit_and_wait(
        session,
        kind=ComputeRequestKind.CREATE_ICEBERG_DATASOURCE,
        runtime_probe=runtime_probe,
        request_json={
            'name': name,
            'description': description,
            'source': source,
            'branch': branch,
            'owner_id': owner_id,
        },
    )
    return datasource_schemas.DataSourceResponse.model_validate(completed.response_json)


async def refresh_datasource(
    session: Session,
    *,
    datasource_id: str,
    runtime_probe: RuntimeAvailabilityProbe,
) -> datasource_schemas.DataSourceResponse:
    completed = await _submit_and_wait(
        session,
        kind=ComputeRequestKind.REFRESH_DATASOURCE,
        request_json={'datasource_id': datasource_id},
        runtime_probe=runtime_probe,
    )
    return datasource_schemas.DataSourceResponse.model_validate(completed.response_json)


async def spawn_engine(
    session: Session,
    *,
    analysis_id: str,
    runtime_probe: RuntimeAvailabilityProbe,
    resource_config: dict[str, object] | None,
) -> compute_schemas.EngineStatusSchema:
    completed = await _submit_and_wait(
        session,
        kind=ComputeRequestKind.SPAWN_ENGINE,
        request_json={'analysis_id': analysis_id, 'resource_config': resource_config or {}},
        runtime_probe=runtime_probe,
    )
    return compute_schemas.EngineStatusSchema.model_validate(completed.response_json)


async def configure_engine(
    session: Session,
    *,
    analysis_id: str,
    runtime_probe: RuntimeAvailabilityProbe,
    resource_config: dict[str, object],
) -> compute_schemas.EngineStatusSchema:
    completed = await _submit_and_wait(
        session,
        kind=ComputeRequestKind.CONFIGURE_ENGINE,
        request_json={'analysis_id': analysis_id, 'resource_config': resource_config},
        runtime_probe=runtime_probe,
    )
    return compute_schemas.EngineStatusSchema.model_validate(completed.response_json)


async def shutdown_engine(
    session: Session,
    *,
    analysis_id: str,
    runtime_probe: RuntimeAvailabilityProbe,
) -> None:
    await _submit_and_wait(
        session,
        kind=ComputeRequestKind.SHUTDOWN_ENGINE,
        request_json={'analysis_id': analysis_id},
        runtime_probe=runtime_probe,
    )
