from __future__ import annotations

import asyncio
import contextlib
import logging
from dataclasses import dataclass
from pathlib import Path

import compute_service as service
from compute_manager import ProcessManager
from fastapi import HTTPException
from sqlmodel import Session
from worker_runtime import runtime_namespaces

from contracts.compute import schemas as compute_schemas
from contracts.compute_requests.live import request_hub
from contracts.compute_requests.models import ComputeRequestKind
from contracts.runtime import ipc as runtime_ipc
from core import compute_requests_service
from core.config import settings
from core.database import get_db, run_db
from core.error_handlers import EXCEPTION_STATUS_MAP
from core.exceptions import AppError, EngineNotFoundError
from core.namespace import reset_namespace, set_namespace_context

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClaimedComputeRequest:
    id: str
    namespace: str
    kind: ComputeRequestKind
    request_json: dict[str, object]


def next_compute_request(worker_id: str, *, lease_seconds: int = 30) -> ClaimedComputeRequest | None:
    for namespace in runtime_namespaces():
        token = set_namespace_context(namespace)
        try:

            def _claim(session: Session) -> ClaimedComputeRequest | None:
                request = compute_requests_service.claim_next_request(session, worker_id=worker_id, lease_seconds=lease_seconds)
                if request is None:
                    return None
                return ClaimedComputeRequest(
                    id=request.id,
                    namespace=request.namespace,
                    kind=request.kind,
                    request_json=request.request_json,
                )

            claimed = run_db(_claim)
        finally:
            reset_namespace(token)
        if claimed is not None:
            return claimed
    return None


async def compute_request_loop(
    stop_event: asyncio.Event,
    *,
    worker_id: str,
    manager: ProcessManager,
    lease_seconds: int = 30,
) -> None:
    last_seen = request_hub.version()
    while not stop_event.is_set():
        handled = await _run_once(worker_id=worker_id, manager=manager, lease_seconds=lease_seconds)
        if handled:
            last_seen = request_hub.version()
            continue
        wait_task = asyncio.create_task(request_hub.wait(last_seen))
        stop_task = asyncio.create_task(stop_event.wait())
        done, pending = await asyncio.wait({wait_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        if stop_task in done:
            return
        with contextlib.suppress(asyncio.CancelledError):
            value = await wait_task
            if isinstance(value, int):
                last_seen = value


async def _run_once(*, worker_id: str, manager: ProcessManager, lease_seconds: int) -> bool:
    claimed = next_compute_request(worker_id, lease_seconds=lease_seconds)
    if claimed is None:
        return False

    renew_stop = asyncio.Event()
    renew_task = asyncio.create_task(_renew_request_lease_loop(claimed.namespace, claimed.id, worker_id, renew_stop, lease_seconds))
    try:
        await _execute_request(claimed, manager)
    finally:
        renew_stop.set()
        with contextlib.suppress(asyncio.CancelledError):
            await renew_task
    return True


async def _renew_request_lease_loop(namespace: str, request_id: str, worker_id: str, stop_event: asyncio.Event, lease_seconds: int) -> None:
    interval = max(1.0, lease_seconds / 2)
    while not stop_event.is_set():
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        if stop_event.is_set():
            return
        token = set_namespace_context(namespace)
        try:
            run_db(compute_requests_service.renew_request_lease, request_id, worker_id=worker_id, lease_seconds=lease_seconds)
        finally:
            reset_namespace(token)


async def _execute_request(claimed: ClaimedComputeRequest, manager: ProcessManager) -> None:
    token = set_namespace_context(claimed.namespace)
    session_gen = get_db()
    session = next(session_gen)
    try:
        if claimed.kind == ComputeRequestKind.PREVIEW:
            preview_request = compute_schemas.StepPreviewRequest.model_validate(claimed.request_json)
            preview_response = service.preview_step(
                session=session,
                manager=manager,
                target_step_id=preview_request.target_step_id,
                analysis_pipeline=preview_request.analysis_pipeline.model_dump(mode='json'),
                row_limit=preview_request.row_limit,
                page=preview_request.page,
                analysis_id=preview_request.analysis_id,
                resource_config=preview_request.resource_config.model_dump() if preview_request.resource_config else None,
                tab_id=preview_request.tab_id,
                request_json=preview_request.model_dump(mode='json'),
            )
            compute_requests_service.mark_request_completed(
                session,
                claimed.id,
                response_json=preview_response.model_dump(mode='json'),
            )
        elif claimed.kind == ComputeRequestKind.SCHEMA:
            schema_request = compute_schemas.StepSchemaRequest.model_validate(claimed.request_json)
            if schema_request.analysis_id is None:
                raise ValueError('analysis_id is required')
            schema_response = service.get_step_schema(
                session=session,
                manager=manager,
                target_step_id=schema_request.target_step_id,
                analysis_id=schema_request.analysis_id,
                analysis_pipeline=schema_request.analysis_pipeline.model_dump(mode='json'),
                tab_id=schema_request.tab_id,
            )
            compute_requests_service.mark_request_completed(
                session,
                claimed.id,
                response_json=schema_response.model_dump(mode='json'),
            )
        elif claimed.kind == ComputeRequestKind.ROW_COUNT:
            row_count_request = compute_schemas.StepRowCountRequest.model_validate(claimed.request_json)
            if row_count_request.analysis_id is None:
                raise ValueError('analysis_id is required')
            row_count_response = service.get_step_row_count(
                session=session,
                manager=manager,
                target_step_id=row_count_request.target_step_id,
                analysis_id=row_count_request.analysis_id,
                analysis_pipeline=row_count_request.analysis_pipeline.model_dump(mode='json'),
                tab_id=row_count_request.tab_id,
                request_json=row_count_request.model_dump(mode='json'),
            )
            compute_requests_service.mark_request_completed(
                session,
                claimed.id,
                response_json=row_count_response.model_dump(mode='json'),
            )
        elif claimed.kind == ComputeRequestKind.DOWNLOAD:
            download_request = compute_schemas.DownloadRequest.model_validate(claimed.request_json)
            file_bytes, filename, content_type = service.download_step(
                session=session,
                manager=manager,
                target_step_id=download_request.target_step_id,
                analysis_pipeline=download_request.analysis_pipeline.model_dump(mode='json'),
                export_format=download_request.format.value,
                filename=download_request.filename,
                analysis_id=download_request.analysis_id,
                tab_id=download_request.tab_id,
            )
            artifact_path = _write_artifact(claimed.id, filename, file_bytes)
            compute_requests_service.mark_request_completed(
                session,
                claimed.id,
                artifact_path=str(artifact_path),
                artifact_name=filename,
                artifact_content_type=content_type,
            )
        elif claimed.kind == ComputeRequestKind.EXPORT:
            export_request = compute_schemas.ExportRequest.model_validate(claimed.request_json)
            result = service.export_data(
                session=session,
                manager=manager,
                target_step_id=export_request.target_step_id,
                analysis_pipeline=export_request.analysis_pipeline.model_dump(mode='json'),
                filename=export_request.filename,
                iceberg_options=export_request.iceberg_options.model_dump() if export_request.iceberg_options else None,
                analysis_id=export_request.analysis_id,
                tab_id=export_request.tab_id,
                request_json=export_request.model_dump(mode='json'),
                result_id=export_request.result_id,
            )
            export_response = compute_schemas.ExportResponse(
                success=True,
                filename=result.datasource_name,
                format='iceberg',
                destination=export_request.destination.value,
                message=f'Created datasource {result.datasource_name}',
                datasource_id=result.datasource_id,
                datasource_name=result.result_meta.get('datasource_name') if isinstance(result.result_meta, dict) else None,
            )
            compute_requests_service.mark_request_completed(
                session,
                claimed.id,
                response_json=export_response.model_dump(mode='json'),
            )
        elif claimed.kind == ComputeRequestKind.SPAWN_ENGINE:
            analysis_id = str(claimed.request_json['analysis_id'])
            resource_config = claimed.request_json.get('resource_config')
            manager.spawn_engine(analysis_id, resource_config=resource_config if isinstance(resource_config, dict) else None)
            response = compute_schemas.EngineStatusSchema.model_validate(manager.get_engine_status(analysis_id))
            compute_requests_service.mark_request_completed(session, claimed.id, response_json=response.model_dump(mode='json'))
        elif claimed.kind == ComputeRequestKind.KEEPALIVE_ENGINE:
            analysis_id = str(claimed.request_json['analysis_id'])
            info = manager.keepalive(analysis_id)
            if info is None:
                raise EngineNotFoundError(analysis_id)
            response = compute_schemas.EngineStatusSchema.model_validate(manager.get_engine_status(analysis_id))
            compute_requests_service.mark_request_completed(session, claimed.id, response_json=response.model_dump(mode='json'))
        elif claimed.kind == ComputeRequestKind.CONFIGURE_ENGINE:
            analysis_id = str(claimed.request_json['analysis_id'])
            resource_config = claimed.request_json.get('resource_config')
            if not isinstance(resource_config, dict):
                raise ValueError('resource_config is required')
            manager.restart_engine_with_config(analysis_id, resource_config)
            response = compute_schemas.EngineStatusSchema.model_validate(manager.get_engine_status(analysis_id))
            compute_requests_service.mark_request_completed(session, claimed.id, response_json=response.model_dump(mode='json'))
        elif claimed.kind == ComputeRequestKind.SHUTDOWN_ENGINE:
            analysis_id = str(claimed.request_json['analysis_id'])
            engine = manager.get_engine(analysis_id)
            if engine is None:
                raise EngineNotFoundError(analysis_id)
            if engine.current_job_id and engine.is_process_alive():
                raise HTTPException(status_code=409, detail='Engine has an active job')
            manager.shutdown_engine(analysis_id)
            compute_requests_service.mark_request_completed(session, claimed.id, response_json={'success': True})
        else:
            raise ValueError(f'Unsupported compute request kind: {claimed.kind.value}')
    except Exception as exc:
        payload = _error_payload(exc)
        status_code = payload.get('status_code')
        if isinstance(status_code, int) and status_code >= 500:
            logger.error('Compute request %s failed: %s', claimed.id, exc, exc_info=True)
        elif isinstance(status_code, int) and status_code >= 400:
            logger.info('Compute request %s rejected: %s', claimed.id, exc)
        else:
            logger.warning('Compute request %s failed: %s', claimed.id, exc)
        compute_requests_service.mark_request_failed(
            session,
            claimed.id,
            error_message=_error_message(exc),
            response_json=payload,
        )
    finally:
        session.close()
        session_gen.close()
        reset_namespace(token)
        await asyncio.to_thread(runtime_ipc.notify_compute_response, claimed.id)


def _write_artifact(request_id: str, filename: str, content: bytes) -> Path:
    directory = Path(settings.data_dir) / 'runtime-compute-downloads'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{request_id}-{filename}'
    path.write_bytes(content)
    return path


def _error_message(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        return str(exc.detail)
    if isinstance(exc, AppError):
        return exc.message
    return str(exc)


def _error_payload(exc: Exception) -> dict[str, object]:
    if isinstance(exc, HTTPException):
        return {'error': str(exc.detail), 'status_code': exc.status_code}
    if isinstance(exc, AppError):
        return {
            'error': exc.message,
            'status_code': EXCEPTION_STATUS_MAP.get(type(exc), 500),
            'error_code': exc.error_code,
            'details': exc.details or {},
        }
    if isinstance(exc, ValueError):
        return {'error': str(exc), 'status_code': 400}
    return {'error': 'An internal error occurred', 'status_code': 500}
