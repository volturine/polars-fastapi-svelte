import asyncio
import contextlib
import logging
import uuid
from urllib.parse import quote

import compute_service as service
from compute_live import ActiveBuild, ActiveBuildContext, registry as build_registry
from compute_manager import ProcessManager
from engine_live import load_engine_snapshot, registry as engine_registry
from fastapi import Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from sqlmodel import Session
from starlette.websockets import WebSocketState

from contracts.auth_models import User
from contracts.build_runs.live import BuildNotification, hub as build_hub
from contracts.compute import schemas
from contracts.engine_runs.schemas import EngineRunKind, EngineRunStatus
from contracts.runtime import ipc as runtime_ipc
from core import build_jobs_service as build_job_service, build_runs_service as build_run_service, engine_runs_service as engine_run_service
from core.config import settings
from core.database import get_db, get_settings_db
from core.error_handlers import handle_errors
from core.exceptions import EngineNotFoundError
from core.namespace import get_namespace, reset_namespace, set_namespace_context
from core.validation import AnalysisId, DataSourceId, EngineRunId, parse_analysis_id, parse_datasource_id, parse_engine_run_id


def get_current_user() -> None:
    return None


def get_manager(request: Request) -> ProcessManager:
    return request.app.state.manager


class MCPRouter:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def get(self, *args, **kwargs):
        return lambda func: func

    def post(self, *args, **kwargs):
        return lambda func: func

    def delete(self, *args, **kwargs):
        return lambda func: func

    def websocket(self, *args, **kwargs):
        return lambda func: func


logger = logging.getLogger(__name__)

router = MCPRouter(prefix='/compute', tags=['compute'])


def _websocket_disconnected(websocket: WebSocket) -> bool:
    return websocket.client_state is WebSocketState.DISCONNECTED or websocket.application_state is WebSocketState.DISCONNECTED


def _is_disconnect_runtime_error(exc: RuntimeError) -> bool:
    message = str(exc)
    return (
        'Cannot call "receive" once a disconnect message has been received' in message
        or 'Cannot call "send" once a close message has been sent' in message
        or ('Unexpected ASGI message' in message and 'websocket.close' in message)
    )


async def _safe_close_websocket(websocket: WebSocket) -> None:
    if _websocket_disconnected(websocket):
        return
    try:
        await websocket.close()
    except RuntimeError as exc:
        if _is_disconnect_runtime_error(exc):
            return
        raise


async def _safe_send_json(websocket: WebSocket, payload: dict) -> bool:
    if _websocket_disconnected(websocket):
        return False
    try:
        await websocket.send_json(payload)
    except RuntimeError as exc:
        if _websocket_disconnected(websocket) or _is_disconnect_runtime_error(exc):
            return False
        raise
    except WebSocketDisconnect:
        return False
    return True


async def _wait_for_websocket_disconnect(websocket: WebSocket) -> None:
    while not _websocket_disconnected(websocket):
        try:
            message = await websocket.receive()
        except WebSocketDisconnect:
            return
        except RuntimeError as exc:
            if _websocket_disconnected(websocket) or _is_disconnect_runtime_error(exc):
                return
            raise
        if message.get('type') == 'websocket.disconnect':
            return


def _get_websocket_manager(websocket: WebSocket) -> ProcessManager:
    return websocket.app.state.manager


def _resolve_websocket_session_token(websocket: WebSocket) -> str | None:
    cookie_token = websocket.cookies.get('session_token')
    if cookie_token:
        return cookie_token
    header_token = websocket.headers.get('X-Session-Token')
    if header_token:
        return header_token
    return None


def _resolve_websocket_user(websocket: WebSocket) -> User | None:
    override = websocket.app.dependency_overrides.get(get_current_user)
    if override is not None:
        return override()

    return None


async def _emit_active_build_event(
    build_id: str,
    analysis_id: str,
    payload: schemas.BuildEvent,
) -> None:
    build = await build_registry.get_build(build_id)
    namespace = build.namespace if build is not None else get_namespace()
    token = set_namespace_context(namespace)
    session_gen = get_db()
    session = next(session_gen)
    try:
        event_row = build_run_service.append_build_event(
            session,
            build_id=build_id,
            event=payload,
            resource_config_json=(
                build.resource_config.model_dump(mode='json') if build is not None and build.resource_config is not None else None
            ),
        )
    finally:
        session.close()
        session_gen.close()
        reset_namespace(token)
    if event_row is None:
        return
    normalized = build_run_service.serialize_event_row(event_row)
    context = await build_registry.apply_event(build_id, normalized)
    if context is not None:
        normalized.update(context.payload())
        await build_registry.publish(build_id, normalized)
    await _publish_build_notification(namespace, build_id, latest_sequence=event_row.sequence)


async def _publish_build_notification(namespace: str, build_id: str, latest_sequence: int) -> None:
    await build_hub.publish(
        BuildNotification(
            namespace=namespace,
            build_id=build_id,
            latest_sequence=latest_sequence,
        )
    )
    await asyncio.to_thread(runtime_ipc.notify_api_build, namespace, build_id, latest_sequence)


def _get_durable_build_detail(session: Session, build_id: str) -> schemas.ActiveBuildDetail | None:
    build_run = build_run_service.get_build_run(session, build_id)
    if build_run is None or build_run.namespace != get_namespace():
        return None
    return build_run_service.fold_build_detail(session, build_run)


def _list_durable_active_builds(session: Session, namespace: str) -> list[schemas.ActiveBuildSummary]:
    runs = build_run_service.list_build_runs(session)
    visible = [run for run in runs if run.namespace == namespace]
    return [
        build_run_service.build_summary(run)
        for run in visible
        if run.status in {build_run_service.BuildRunStatus.QUEUED, build_run_service.BuildRunStatus.RUNNING}
    ]


def _build_snapshot_message(session: Session, build_id: str) -> schemas.BuildSnapshotMessage | None:
    detail = _get_durable_build_detail(session, build_id)
    if detail is None:
        return None
    return schemas.BuildSnapshotMessage(build=detail, last_sequence=build_run_service.get_latest_sequence(session, build_id))


def _build_list_snapshot_message(session: Session, namespace: str) -> schemas.BuildListSnapshotMessage:
    return schemas.BuildListSnapshotMessage(builds=_list_durable_active_builds(session, namespace))


async def _replay_build_events(websocket: WebSocket, build_id: str, after_sequence: int) -> int | None:
    session_gen = get_db()
    session = next(session_gen)
    try:
        rows = build_run_service.list_build_events_after(session, build_id, after_sequence)
    finally:
        session.close()
        session_gen.close()
    latest = after_sequence
    for row in rows:
        if not await _safe_send_json(websocket, build_run_service.serialize_event_row(row)):
            return None
        latest = row.sequence
    return latest


async def _wait_for_build_notification(websocket: WebSocket, build_id: str, last_sequence: int = 0) -> BuildNotification | None:
    receive_task = asyncio.create_task(_wait_for_websocket_disconnect(websocket))
    notify_task = asyncio.create_task(build_hub.wait_for_build(build_id, last_sequence))
    done, pending = await asyncio.wait({receive_task, notify_task}, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    for task in pending:
        with contextlib.suppress(asyncio.CancelledError):
            await task
    if receive_task in done:
        await receive_task
        return None
    return await notify_task


async def _wait_for_namespace_build_update(websocket: WebSocket, namespace: str, last_seen: str | None) -> str | None:
    last_version = int(last_seen) if last_seen and last_seen.isdigit() else 0
    receive_task = asyncio.create_task(_wait_for_websocket_disconnect(websocket))
    notify_task = asyncio.create_task(build_hub.wait_for_namespace(namespace, last_version))
    done, pending = await asyncio.wait({receive_task, notify_task}, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    for task in pending:
        with contextlib.suppress(asyncio.CancelledError):
            await task
    if receive_task in done:
        await receive_task
        return None
    await notify_task
    latest_version = build_hub.latest_namespace_sequence(namespace)
    if latest_version > last_version:
        return str(latest_version)
    return last_seen


def _get_durable_build_detail_by_engine_run(session: Session, engine_run_id: str) -> schemas.ActiveBuildDetail | None:
    build_run = build_run_service.get_build_run_by_engine_run(session, engine_run_id)
    if build_run is None or build_run.namespace != get_namespace():
        return None
    return build_run_service.fold_build_detail(session, build_run)


async def _require_websocket_user(websocket: WebSocket) -> User:
    user = await run_in_threadpool(_resolve_websocket_user, websocket)
    if user is None:
        raise HTTPException(status_code=401, detail='Not authenticated')
    return user


def _build_analysis_name(pipeline: dict) -> str:
    analysis_id = pipeline.get('analysis_id')
    if not isinstance(analysis_id, str) or not analysis_id:
        return 'Build'
    session_gen = get_db()
    session = next(session_gen)
    try:
        return service._analysis_name(session, analysis_id)
    finally:
        session.close()
        session_gen.close()


def _build_triggered_by(user: User | None) -> str:
    if user is None:
        return 'user'
    return user.id


async def _send_build_snapshot(websocket: WebSocket, build_id: str) -> None:
    session_gen = get_db()
    session = next(session_gen)
    try:
        message = _build_snapshot_message(session, build_id)
    finally:
        session.close()
        session_gen.close()
    if message is None:
        raise HTTPException(status_code=404, detail='Active build not found')
    await _safe_send_json(websocket, message.model_dump(mode='json'))


async def _send_build_list_snapshot(websocket: WebSocket, namespace: str) -> None:
    session_gen = get_db()
    session = next(session_gen)
    try:
        message = _build_list_snapshot_message(session, namespace)
    finally:
        session.close()
        session_gen.close()
    await _safe_send_json(websocket, message.model_dump(mode='json'))


def _get_latest_build_namespace_update(namespace: str) -> str | None:
    latest = build_hub.latest_namespace_sequence(namespace)
    if latest <= 0:
        return None
    return str(latest)


async def _send_engine_snapshot(websocket: WebSocket, manager: ProcessManager) -> None:
    del manager
    session_gen = get_settings_db()
    session = next(session_gen)
    try:
        defaults: dict[str, object] = {
            'max_threads': settings.polars_max_threads,
            'max_memory_mb': settings.polars_max_memory_mb,
            'streaming_chunk_size': settings.polars_streaming_chunk_size,
        }
        message = load_engine_snapshot(session, namespace=get_namespace(), defaults=defaults)
    finally:
        session.close()
        session_gen.close()
    await _safe_send_json(websocket, message.model_dump(mode='json'))


async def _wait_for_engine_notification(websocket: WebSocket, namespace: str, last_seen: str | None) -> str | None:
    receive_task = asyncio.create_task(_wait_for_websocket_disconnect(websocket))
    notify_task = asyncio.create_task(engine_registry.wait_for_namespace(namespace, last_seen))
    done, pending = await asyncio.wait({receive_task, notify_task}, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    for task in pending:
        with contextlib.suppress(asyncio.CancelledError):
            await task
    if receive_task in done:
        await receive_task
        return None
    return await notify_task


def _build_pipeline_payload(request: schemas.BuildRequest) -> dict:
    pipeline = request.analysis_pipeline.model_dump(mode='json') if request.analysis_pipeline else None
    if not isinstance(pipeline, dict):
        raise ValueError('analysis_pipeline is required')
    return {**pipeline, 'tab_id': request.tab_id}


async def _run_active_build_task(
    *,
    manager: ProcessManager,
    build_id: str,
    analysis_id: str,
    namespace: str,
    pipeline: dict,
    triggered_by: str | None,
) -> None:
    token = set_namespace_context(namespace)
    session_gen = None
    session = None
    try:
        build = await build_registry.get_build(build_id)
        if build is None:
            return
        active_build = build
        session_gen = get_db()
        session = next(session_gen)
        await service.run_analysis_build_stream(
            session=session,
            manager=manager,
            pipeline=pipeline,
            build=active_build,
            emitter=lambda payload: _emit_active_build_event(active_build.build_id, analysis_id, payload),
            triggered_by=triggered_by,
        )
    except Exception as exc:
        logger.error('Active build task error: %s', exc, exc_info=True)
        build = await build_registry.get_build(build_id)
        if build is not None and build.status == schemas.ActiveBuildStatus.RUNNING:
            await _emit_active_build_event(
                build.build_id,
                analysis_id,
                schemas.BuildFailedEvent(
                    build_id=build.build_id,
                    analysis_id=analysis_id,
                    emitted_at=service._utcnow(),
                    current_kind=build.current_kind,
                    current_datasource_id=build.current_datasource_id,
                    tab_id=build.current_tab_id,
                    tab_name=build.current_tab_name,
                    current_output_id=build.current_output_id,
                    current_output_name=build.current_output_name,
                    engine_run_id=build.current_engine_run_id,
                    progress=build.progress,
                    elapsed_ms=build.elapsed_ms,
                    total_steps=build.total_steps,
                    tabs_built=len(build.results),
                    results=build.results,
                    duration_ms=build.elapsed_ms,
                    error='Build failed due to an internal error',
                ),
            )
    finally:
        if session is not None:
            session.close()
        if session_gen is not None:
            session_gen.close()
        reset_namespace(token)


async def _run_queued_build_job(*, manager: ProcessManager, build_id: str) -> None:
    session_gen = get_db()
    session = next(session_gen)
    build: ActiveBuild | None = None
    pipeline: dict | None = None
    starter: schemas.BuildStarter | None = None
    request_payload: schemas.BuildRequest | None = None
    namespace = get_namespace()
    try:
        run = build_run_service.get_build_run(session, build_id)
        if run is None:
            return
        marked = build_run_service.mark_build_running(session, build_id, now=service._utcnow())
        if marked is None:
            return
        request_payload = schemas.BuildRequest.model_validate(run.request_json)
        pipeline = _build_pipeline_payload(request_payload)
        starter = schemas.BuildStarter.model_validate(run.starter_json)
        namespace = run.namespace
        context = ActiveBuildContext(
            current_kind=run.current_kind,
            current_datasource_id=run.current_datasource_id,
            current_tab_id=run.current_tab_id,
            current_tab_name=run.current_tab_name,
            current_output_id=run.current_output_id,
            current_output_name=run.current_output_name,
        )
        build = await build_registry.create_build(
            analysis_id=run.analysis_id,
            analysis_name=run.analysis_name,
            namespace=namespace,
            starter=starter,
            total_tabs=run.total_tabs,
            context=context,
            build_id=run.id,
            started_at=run.started_at,
        )
        build.status = schemas.ActiveBuildStatus.RUNNING
    finally:
        session.close()
        session_gen.close()
    if build is None or pipeline is None or starter is None or request_payload is None:
        return
    await _publish_build_notification(namespace, build_id, latest_sequence=0)
    current_kind = build.current_kind or ''
    if current_kind in {'raw', 'datasource_update'}:
        datasource_id = build.current_datasource_id
        if datasource_id is None:
            raise ValueError(f'Queued schedule build {build.build_id} missing datasource id')
        session_gen = get_db()
        session = next(session_gen)
        try:
            try:
                import datasource_service

                if current_kind == 'raw':
                    refreshed = await asyncio.to_thread(datasource_service.refresh_external_datasource, session, datasource_id)
                else:
                    refreshed = await asyncio.to_thread(
                        datasource_service.refresh_datasource_for_schedule,
                        session,
                        datasource_id,
                    )
                await _emit_active_build_event(
                    build.build_id,
                    build.analysis_id,
                    schemas.BuildCompleteEvent(
                        build_id=build.build_id,
                        analysis_id=build.analysis_id,
                        emitted_at=service._utcnow(),
                        current_kind=build.current_kind,
                        current_datasource_id=build.current_datasource_id,
                        tab_id=build.current_tab_id,
                        tab_name=build.current_tab_name,
                        current_output_id=build.current_output_id,
                        current_output_name=refreshed.name,
                        engine_run_id=None,
                        elapsed_ms=build.elapsed_ms,
                        total_steps=0,
                        tabs_built=1,
                        results=[
                            schemas.BuildTabResult(
                                tab_id=build.current_tab_id or build.build_id,
                                tab_name=build.current_tab_name or refreshed.name,
                                status=schemas.BuildTabStatus.SUCCESS,
                                output_id=build.current_output_id,
                                output_name=refreshed.name,
                            )
                        ],
                        duration_ms=build.elapsed_ms,
                    ),
                )
                return
            except Exception as exc:
                await _emit_active_build_event(
                    build.build_id,
                    build.analysis_id,
                    schemas.BuildFailedEvent(
                        build_id=build.build_id,
                        analysis_id=build.analysis_id,
                        emitted_at=service._utcnow(),
                        current_kind=build.current_kind,
                        current_datasource_id=build.current_datasource_id,
                        tab_id=build.current_tab_id,
                        tab_name=build.current_tab_name,
                        current_output_id=build.current_output_id,
                        current_output_name=build.current_output_name,
                        engine_run_id=None,
                        progress=build.progress,
                        elapsed_ms=build.elapsed_ms,
                        total_steps=0,
                        tabs_built=0,
                        results=[],
                        duration_ms=build.elapsed_ms,
                        error=str(exc),
                    ),
                )
                return
        finally:
            session.close()
            session_gen.close()
    await _run_active_build_task(
        manager=manager,
        build_id=build.build_id,
        analysis_id=build.analysis_id,
        namespace=build.namespace,
        pipeline=pipeline,
        triggered_by=starter.user_id or starter.email or starter.display_name or starter.triggered_by,
    )


@router.post('/preview', response_model=schemas.StepPreviewResponse, mcp=True)
@handle_errors(operation='preview step')
def preview_step(
    request: schemas.StepPreviewRequest,
    session: Session = Depends(get_db),
    manager: ProcessManager = Depends(get_manager),
):
    """Preview the result of a pipeline step with pagination.

    Requires analysis_pipeline (full pipeline payload with tabs and steps) and target_step_id
    (the step to preview, or 'source' for raw data). Returns column names, types, data rows,
    and total row count. Use row_limit and page for pagination.
    """
    analysis_id = request.analysis_id if request.analysis_id is not None else request.analysis_pipeline.analysis_id

    return service.preview_step(
        session=session,
        manager=manager,
        target_step_id=request.target_step_id,
        analysis_pipeline=request.analysis_pipeline.model_dump(mode='json'),
        row_limit=request.row_limit,
        page=request.page,
        analysis_id=analysis_id,
        resource_config=request.resource_config.model_dump() if request.resource_config else None,
        tab_id=request.tab_id,
        request_json=request.model_dump(mode='json'),
    )


@router.post('/schema', response_model=schemas.StepSchemaResponse, mcp=True)
@handle_errors(operation='get step schema')
def get_step_schema(
    request: schemas.StepSchemaRequest,
    session: Session = Depends(get_db),
    manager: ProcessManager = Depends(get_manager),
):
    """Get the output column schema of a pipeline step without fetching data.

    Useful for configuring downstream steps that need to know available columns
    (e.g., pivot, unpivot, select). Returns column names and their Polars dtypes.
    """
    analysis_id = request.analysis_id if request.analysis_id is not None else request.analysis_pipeline.analysis_id

    return service.get_step_schema(
        session=session,
        manager=manager,
        target_step_id=request.target_step_id,
        analysis_id=analysis_id,
        analysis_pipeline=request.analysis_pipeline.model_dump(mode='json'),
        tab_id=request.tab_id,
    )


@router.post('/row-count', response_model=schemas.StepRowCountResponse, mcp=True)
@handle_errors(operation='get step row count')
def get_step_row_count(
    request: schemas.StepRowCountRequest,
    session: Session = Depends(get_db),
    manager: ProcessManager = Depends(get_manager),
):
    """Get the row count of a pipeline step result without fetching data. Faster than a full preview."""
    analysis_id = request.analysis_id if request.analysis_id is not None else request.analysis_pipeline.analysis_id

    return service.get_step_row_count(
        session=session,
        manager=manager,
        target_step_id=request.target_step_id,
        analysis_id=analysis_id,
        analysis_pipeline=request.analysis_pipeline.model_dump(mode='json'),
        tab_id=request.tab_id,
        request_json=request.model_dump(mode='json'),
    )


@router.get('/iceberg/{datasource_id}/snapshots', response_model=schemas.IcebergSnapshotsResponse, mcp=True)
@handle_errors(operation='list iceberg snapshots')
def list_iceberg_snapshots(
    datasource_id: DataSourceId,
    branch: str | None = None,
    session: Session = Depends(get_db),
):
    """List Iceberg table snapshots for time-travel selection.

    Each snapshot has a snapshot_id, timestamp, and operation type.
    Optionally filter by branch. Use snapshot_id with compare-snapshots.
    """
    return service.list_iceberg_snapshots(session, parse_datasource_id(datasource_id), branch=branch)


@router.delete(
    '/iceberg/{datasource_id}/snapshots/{snapshot_id}',
    response_model=schemas.IcebergSnapshotDeleteResponse,
    mcp=True,
)
@handle_errors(operation='delete iceberg snapshot')
def delete_iceberg_snapshot(
    datasource_id: DataSourceId,
    snapshot_id: int,
    session: Session = Depends(get_db),
):
    """Delete an Iceberg snapshot by ID. Use GET /compute/iceberg/{id}/snapshots to find snapshot IDs.

    Warning: deleting snapshots removes the ability to time-travel to that point.
    """
    return service.delete_iceberg_snapshot(session, parse_datasource_id(datasource_id), str(snapshot_id))


@router.post('/builds/active', response_model=schemas.ActiveBuildDetail)
@handle_errors(operation='start active build')
async def start_active_build(
    request: schemas.BuildRequest,
    session: Session = Depends(get_db),
    _manager: ProcessManager = Depends(get_manager),
    user: User = Depends(get_current_user),
):
    pipeline = _build_pipeline_payload(request)
    analysis_id = str(pipeline.get('analysis_id') or '')
    analysis_name = await run_in_threadpool(_build_analysis_name, pipeline)
    namespace = get_namespace()
    started_at = service._utcnow()
    build_id = str(uuid.uuid4())
    raw_tabs = pipeline.get('tabs')
    tabs = raw_tabs if isinstance(raw_tabs, list) else []
    selected_tab = next(
        (tab for tab in tabs if isinstance(tab, dict) and isinstance(tab.get('id'), str) and tab.get('id') == request.tab_id),
        None,
    )
    active_tab = selected_tab if isinstance(selected_tab, dict) else next((tab for tab in tabs if isinstance(tab, dict)), None)
    context = ActiveBuildContext(
        current_kind=EngineRunKind.PREVIEW.value,
        current_datasource_id=None,
        current_tab_id=None,
        current_tab_name=None,
        current_output_id=None,
        current_output_name=None,
    )
    if isinstance(active_tab, dict):
        datasource = active_tab.get('datasource')
        if isinstance(datasource, dict) and isinstance(datasource.get('id'), str):
            context.current_datasource_id = datasource.get('id')
        if isinstance(active_tab.get('id'), str):
            context.current_tab_id = active_tab.get('id')
        if isinstance(active_tab.get('name'), str):
            context.current_tab_name = active_tab.get('name')
    starter = service._build_starter(user)
    build_run_service.create_build_run(
        session,
        build_id=build_id,
        namespace=namespace,
        analysis_id=analysis_id,
        analysis_name=analysis_name,
        request_json=request.model_dump(mode='json'),
        starter_json=starter.model_dump(mode='json'),
        status=build_run_service.BuildRunStatus.QUEUED,
        current_kind=context.current_kind,
        current_datasource_id=context.current_datasource_id,
        current_tab_id=context.current_tab_id,
        current_tab_name=context.current_tab_name,
        current_output_id=context.current_output_id,
        current_output_name=context.current_output_name,
        total_tabs=len(tabs),
        created_at=started_at,
        started_at=started_at,
    )
    build_job_service.create_job(
        session,
        build_id=build_id,
        namespace=namespace,
    )
    detail = _get_durable_build_detail(session, build_id)
    if detail is None:
        raise HTTPException(status_code=500, detail='Failed to create build')
    await _publish_build_notification(namespace, build_id, latest_sequence=0)
    from contracts.build_jobs.live import hub as build_job_hub

    build_job_hub.publish()
    await asyncio.to_thread(runtime_ipc.notify_build_job)
    return detail


@router.post('/cancel/{engine_run_id}', response_model=schemas.CancelBuildResponse, mcp=True)
@handle_errors(operation='cancel build')
async def cancel_build(
    engine_run_id: EngineRunId,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run_id = parse_engine_run_id(engine_run_id)
    run = engine_run_service.get_engine_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail='Engine run not found')
    if run.status != EngineRunStatus.RUNNING:
        raise HTTPException(status_code=400, detail='Only running builds can be cancelled')

    cancelled_by = user.email or user.display_name or user.id
    cancelled = service.cancel_engine_run(
        session,
        run_id,
        cancelled_by=cancelled_by,
    )

    active = await build_registry.list_builds()
    match = next(
        (
            item
            for item in active
            if item.namespace == get_namespace()
            and item.current_engine_run_id == run_id
            and item.status == schemas.ActiveBuildStatus.RUNNING
        ),
        None,
    )
    live = await build_registry.get_build(match.build_id) if match is not None else None
    durable = _get_durable_build_detail_by_engine_run(session, run_id)
    target = live.detail() if live is not None and live.namespace == get_namespace() else durable
    if target is not None:
        await _emit_active_build_event(
            target.build_id,
            target.analysis_id,
            schemas.BuildCancelledEvent(
                build_id=target.build_id,
                analysis_id=target.analysis_id,
                emitted_at=service._utcnow(),
                current_kind=target.current_kind,
                current_datasource_id=target.current_datasource_id,
                tab_id=target.current_tab_id,
                tab_name=target.current_tab_name,
                current_output_id=target.current_output_id,
                current_output_name=target.current_output_name,
                engine_run_id=run_id,
                progress=target.progress,
                elapsed_ms=cancelled.duration_ms or target.elapsed_ms,
                total_steps=target.total_steps,
                tabs_built=len(target.results),
                results=target.results,
                duration_ms=cancelled.duration_ms or target.elapsed_ms,
                cancelled_at=cancelled.cancelled_at,
                cancelled_by=cancelled.cancelled_by,
            ),
        )

    return cancelled


@router.get('/builds/active', response_model=schemas.ActiveBuildListResponse, mcp=True)
@handle_errors(operation='list active builds')
async def list_active_builds(
    request: Request,
    status: schemas.ActiveBuildStatus | None = None,
    session: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    del request
    if status not in {None, schemas.ActiveBuildStatus.QUEUED, schemas.ActiveBuildStatus.RUNNING}:
        return schemas.ActiveBuildListResponse(builds=[], total=0)
    runs = build_run_service.list_build_runs(session)
    visible = [
        build_run_service.build_summary(run)
        for run in runs
        if run.namespace == get_namespace()
        and run.status in {build_run_service.BuildRunStatus.QUEUED, build_run_service.BuildRunStatus.RUNNING}
    ]
    return schemas.ActiveBuildListResponse(builds=visible, total=len(visible))


@router.get('/builds/active/{build_id}', response_model=schemas.ActiveBuildDetail, mcp=True)
@handle_errors(operation='get active build')
async def get_active_build(
    build_id: str,
    session: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    detail = _get_durable_build_detail(session, build_id)
    if detail is None:
        raise HTTPException(status_code=404, detail='Active build not found')
    return detail


@router.get('/builds/active/by-engine-run/{engine_run_id}', response_model=schemas.ActiveBuildDetail, mcp=True)
@handle_errors(operation='get active build by engine run')
async def get_active_build_by_engine_run(
    engine_run_id: EngineRunId,
    session: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    run_id = parse_engine_run_id(engine_run_id)
    detail = _get_durable_build_detail_by_engine_run(session, run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail='Active build not found')
    return detail


# Engine lifecycle endpoints


@router.post('/engine/spawn/{analysis_id}', response_model=schemas.EngineStatusSchema, mcp=True)
@handle_errors(operation='spawn engine')
def spawn_engine(
    analysis_id: AnalysisId,
    request: schemas.SpawnEngineRequest | None = None,
    manager: ProcessManager = Depends(get_manager),
):
    """Spawn a compute engine for an analysis (called when analysis page opens).

    Optionally accepts resource configuration overrides.
    """
    resource_config = request.resource_config.model_dump() if request and request.resource_config else None
    analysis_id_value = parse_analysis_id(analysis_id)
    manager.spawn_engine(analysis_id_value, resource_config=resource_config)
    return manager.get_engine_status(analysis_id_value)


@router.post('/engine/keepalive/{analysis_id}', response_model=schemas.EngineStatusSchema, mcp=True)
@handle_errors(operation='keepalive engine')
def keepalive(analysis_id: AnalysisId, manager: ProcessManager = Depends(get_manager)):
    """Send keepalive ping for an analysis engine."""
    analysis_id_value = parse_analysis_id(analysis_id)
    info = manager.keepalive(analysis_id_value)
    if not info:
        raise EngineNotFoundError(analysis_id_value)
    return manager.get_engine_status(analysis_id_value)


@router.post('/engine/configure/{analysis_id}', response_model=schemas.EngineStatusSchema, mcp=True)
@handle_errors(operation='configure engine')
def configure_engine(
    analysis_id: AnalysisId,
    request: schemas.EngineResourceConfig,
    manager: ProcessManager = Depends(get_manager),
):
    """Update engine resource configuration (restarts the engine).

    This will terminate any running jobs and restart the engine with the new
    resource configuration. Values set to null will use the default from settings.
    """
    resource_config = request.model_dump()
    analysis_id_value = parse_analysis_id(analysis_id)
    manager.restart_engine_with_config(analysis_id_value, resource_config)
    return manager.get_engine_status(analysis_id_value)


@router.delete('/engine/{analysis_id}', status_code=204, mcp=True)
@handle_errors(operation='shutdown engine')
def shutdown_engine(analysis_id: AnalysisId, manager: ProcessManager = Depends(get_manager)):
    """Shutdown an analysis engine."""
    analysis_id_value = parse_analysis_id(analysis_id)
    engine = manager.get_engine(analysis_id_value)
    if not engine:
        raise EngineNotFoundError(analysis_id_value)
    if engine.current_job_id and engine.is_process_alive():
        raise HTTPException(status_code=409, detail='Engine has an active job')
    manager.shutdown_engine(analysis_id_value)


@router.websocket('/ws/engines')
async def engine_list_stream(websocket: WebSocket) -> None:
    token = set_namespace_context(websocket.headers.get('X-Namespace') or websocket.query_params.get('namespace'))
    namespace = get_namespace()
    manager = _get_websocket_manager(websocket)
    await websocket.accept()
    try:
        await engine_registry.add_watcher(namespace, websocket)
        last_seen = await engine_registry.current_version(namespace)
        await _send_engine_snapshot(websocket, manager)
        while True:
            updated = await _wait_for_engine_notification(websocket, namespace, last_seen)
            if updated is None:
                return
            await _send_engine_snapshot(websocket, manager)
            last_seen = updated
    except WebSocketDisconnect:
        return
    except HTTPException as exc:
        await _safe_send_json(
            websocket,
            schemas.EngineWebsocketErrorMessage(error=str(exc.detail), status_code=exc.status_code).model_dump(mode='json'),
        )
    except RuntimeError as exc:
        if _is_disconnect_runtime_error(exc):
            return
        logger.error('Engine websocket error: %s', exc, exc_info=True)
        await _safe_send_json(
            websocket,
            schemas.EngineWebsocketErrorMessage(error='An internal error occurred').model_dump(mode='json'),
        )
    except Exception as exc:
        logger.error('Engine websocket error: %s', exc, exc_info=True)
        await _safe_send_json(
            websocket,
            schemas.EngineWebsocketErrorMessage(error='An internal error occurred').model_dump(mode='json'),
        )
    finally:
        await engine_registry.remove_watcher(namespace, websocket)
        reset_namespace(token)
        await _safe_close_websocket(websocket)


@router.websocket('/ws/builds')
async def build_list_stream(websocket: WebSocket) -> None:
    token = set_namespace_context(websocket.headers.get('X-Namespace') or websocket.query_params.get('namespace'))
    namespace = get_namespace()
    await websocket.accept()
    try:
        await _require_websocket_user(websocket)
        last_seen = await run_in_threadpool(_get_latest_build_namespace_update, namespace)
        await _send_build_list_snapshot(websocket, namespace)
        while True:
            updated = await _wait_for_namespace_build_update(websocket, namespace, last_seen)
            if updated is None:
                return
            session_gen = get_db()
            session = next(session_gen)
            try:
                payload = _build_list_snapshot_message(session, namespace).model_dump(mode='json')
            finally:
                session.close()
                session_gen.close()
            sent = await _safe_send_json(websocket, payload)
            if not sent:
                return
            last_seen = updated
    except WebSocketDisconnect:
        return
    except HTTPException as exc:
        await _safe_send_json(
            websocket, schemas.BuildWebsocketErrorMessage(error=str(exc.detail), status_code=exc.status_code).model_dump(mode='json')
        )
    except RuntimeError as exc:
        if _is_disconnect_runtime_error(exc):
            return
        logger.error('Build list websocket error: %s', exc, exc_info=True)
        await _safe_send_json(
            websocket,
            schemas.BuildWebsocketErrorMessage(error='An internal error occurred').model_dump(mode='json'),
        )
    except Exception as exc:
        logger.error('Build list websocket error: %s', exc, exc_info=True)
        await _safe_send_json(
            websocket,
            schemas.BuildWebsocketErrorMessage(error='An internal error occurred').model_dump(mode='json'),
        )
    finally:
        reset_namespace(token)
        await _safe_close_websocket(websocket)


@router.websocket('/ws/builds/{build_id}')
async def active_build_stream(websocket: WebSocket, build_id: str) -> None:
    token = set_namespace_context(websocket.headers.get('X-Namespace') or websocket.query_params.get('namespace'))
    raw_last_sequence = websocket.query_params.get('last_sequence')
    last_sequence = int(raw_last_sequence) if raw_last_sequence and raw_last_sequence.isdigit() else 0
    await websocket.accept()
    try:
        await _require_websocket_user(websocket)
        while True:
            session_gen = get_db()
            session = next(session_gen)
            try:
                message = _build_snapshot_message(session, build_id)
            finally:
                session.close()
                session_gen.close()
            if message is None or message.build.namespace != get_namespace():
                raise HTTPException(status_code=404, detail='Active build not found')
            if message.last_sequence <= last_sequence:
                break
            if last_sequence > 0:
                replayed_sequence = await _replay_build_events(websocket, build_id, last_sequence)
                if replayed_sequence is None:
                    return
                last_sequence = replayed_sequence
                continue
            break
        sent = await _safe_send_json(websocket, message.model_dump(mode='json'))
        if not sent:
            return
        last_sequence = max(last_sequence, message.last_sequence)
        while True:
            notification = await _wait_for_build_notification(websocket, build_id, last_sequence)
            if notification is None:
                return
            replayed_sequence = await _replay_build_events(websocket, build_id, last_sequence)
            if replayed_sequence is None:
                return
            last_sequence = max(replayed_sequence, notification.latest_sequence)
    except WebSocketDisconnect:
        return
    except HTTPException as exc:
        await _safe_send_json(
            websocket, schemas.BuildWebsocketErrorMessage(error=str(exc.detail), status_code=exc.status_code).model_dump(mode='json')
        )
    except RuntimeError as exc:
        if _is_disconnect_runtime_error(exc):
            return
        logger.error('Active build websocket error: %s', exc, exc_info=True)
        await _safe_send_json(
            websocket,
            schemas.BuildWebsocketErrorMessage(error='An internal error occurred').model_dump(mode='json'),
        )
    except Exception as exc:
        logger.error('Active build websocket error: %s', exc, exc_info=True)
        await _safe_send_json(
            websocket,
            schemas.BuildWebsocketErrorMessage(error='An internal error occurred').model_dump(mode='json'),
        )
    finally:
        reset_namespace(token)
        await _safe_close_websocket(websocket)


@router.get('/defaults', response_model=schemas.EngineDefaults, mcp=True)
@handle_errors(operation='get engine defaults')
def get_engine_defaults():
    """Get default engine resource settings from environment configuration."""
    from core.config import settings

    return schemas.EngineDefaults(
        max_threads=settings.polars_max_threads,
        max_memory_mb=settings.polars_max_memory_mb,
        streaming_chunk_size=settings.polars_streaming_chunk_size,
    )


@router.post('/export', mcp=True)
@handle_errors(operation='export data')
def export_data(
    request: schemas.ExportRequest,
    session: Session = Depends(get_db),
    manager: ProcessManager = Depends(get_manager),
):
    """Export pipeline results to a file download or output datasource.

    For destination='download': returns file bytes in the requested format (csv, parquet, json, etc.).
    For destination='datasource': writes to an Iceberg output datasource (requires result_id and iceberg_options).
    """
    if request.destination == schemas.ExportDestination.DOWNLOAD:
        file_bytes, filename, content_type = service.download_step(
            session=session,
            manager=manager,
            target_step_id=request.target_step_id,
            analysis_pipeline=request.analysis_pipeline.model_dump(mode='json'),
            export_format=request.format.value,
            filename=request.filename,
            analysis_id=request.analysis_id,
            tab_id=request.tab_id,
        )
        safe_name = quote(filename)
        return Response(
            content=file_bytes,
            media_type=content_type,
            headers={'Content-Disposition': f'attachment; filename="{safe_name}"'},
        )

    result = service.export_data(
        session=session,
        manager=manager,
        target_step_id=request.target_step_id,
        analysis_pipeline=request.analysis_pipeline.model_dump(mode='json'),
        filename=request.filename,
        iceberg_options=request.iceberg_options.model_dump() if request.iceberg_options else None,
        analysis_id=request.analysis_id,
        tab_id=request.tab_id,
        request_json=request.model_dump(mode='json'),
        result_id=request.result_id,
    )
    return schemas.ExportResponse(
        success=True,
        filename=result.datasource_name,
        format='iceberg',
        destination=request.destination.value,
        message=f'Created datasource {result.datasource_name}',
        datasource_id=result.datasource_id,
        datasource_name=result.result_meta.get('datasource_name') if isinstance(result.result_meta, dict) else None,
    )


@router.post('/download', mcp=True)
@handle_errors(operation='download step')
def download_step(
    request: schemas.DownloadRequest,
    session: Session = Depends(get_db),
    manager: ProcessManager = Depends(get_manager),
):
    """Download pipeline step result as a file.

    Returns the file bytes with appropriate Content-Type header.
    Supported formats: csv, parquet, json, ndjson, duckdb, excel.
    """
    file_bytes, filename, content_type = service.download_step(
        session=session,
        manager=manager,
        target_step_id=request.target_step_id,
        analysis_pipeline=request.analysis_pipeline.model_dump(mode='json'),
        export_format=request.format.value,
        filename=request.filename,
        analysis_id=request.analysis_id,
        tab_id=request.tab_id,
    )

    if file_bytes is None or filename is None or content_type is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail='Download file content not available')

    safe_name = quote(filename)
    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={'Content-Disposition': f'attachment; filename="{safe_name}"'},
    )
