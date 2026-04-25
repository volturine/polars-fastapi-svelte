import asyncio
import contextlib
import logging
import os
import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlmodel import Session, text

from api import router
from core.config import settings
from core.database import get_settings_db, init_db, run_db, run_settings_db, supports_distributed_runtime
from core.error_handlers import app_error_handler, generic_error_handler, validation_error_handler
from core.exceptions import AppError
from core.http import close_clients
from core.logging import RequestLoggingMiddleware, configure_logging
from core.namespace import list_namespaces, namespace_paths, reset_namespace, set_namespace_context
from modules.build_runs import service as build_run_service
from modules.compute.engine_live import create_snapshot_notifier
from modules.compute.manager import ProcessManager
from modules.engine_instances import service as engine_instance_service
from modules.runtime import ipc as runtime_ipc
from modules.runtime_workers import service as runtime_worker_service
from modules.runtime_workers.models import RuntimeWorkerKind
from modules.udf.seed import ensure_udf_seeds

logger = logging.getLogger(__name__)


def _persist_engine_snapshot(worker_id: str, namespace: str, statuses) -> None:
    from core.database import run_settings_db

    def _write(session: Session) -> None:
        engine_instance_service.persist_engine_snapshot(
            session,
            worker_id=worker_id,
            namespace=namespace,
            statuses=list(statuses),
        )

    run_settings_db(_write)


def _register_api_worker(worker_id: str) -> None:
    def _register(session: Session) -> None:
        runtime_worker_service.register_worker(
            session,
            worker_id=worker_id,
            kind=RuntimeWorkerKind.API,
            hostname=socket.gethostname(),
            pid=os.getpid(),
            capacity=max(settings.worker_connections, 1),
        )

    run_settings_db(_register)


def _heartbeat_api_worker(worker_id: str) -> None:
    def _heartbeat(session: Session) -> None:
        runtime_worker_service.heartbeat_worker(session, worker_id=worker_id)

    run_settings_db(_heartbeat)


def _stop_api_worker(worker_id: str) -> None:
    def _stop(session: Session) -> None:
        runtime_worker_service.mark_worker_stopped(session, worker_id=worker_id)

    run_settings_db(_stop)


# Detect Nuitka compiled binary vs running from source.
# In Nuitka-compiled code, __compiled__ is a C-level built-in constant set to True.
# In a regular Python interpreter it is not defined, raising NameError.
try:
    _NUITKA_COMPILED: bool = __compiled__  # type: ignore[name-defined]  # noqa: F821
except NameError:
    _NUITKA_COMPILED = False

if _NUITKA_COMPILED:
    # In a Nuitka onefile binary, data files are extracted alongside __file__
    # into the temporary extraction directory.
    frontend_build_dir = Path(__file__).parent / 'frontend' / 'build'
else:
    # In a regular source checkout, the frontend build lives two levels up
    # from backend/main.py at <repo_root>/frontend/build.
    frontend_build_dir = Path(__file__).parent.parent / 'frontend' / 'build'


def _resolve_uvicorn_workers() -> int:
    if settings.debug:
        return 1
    if settings.workers > 0:
        return settings.workers
    cores = os.cpu_count() or 1
    return max(1, (2 * cores) + 1)


def _guard_runtime_workers(workers: int) -> int:
    if workers <= 1:
        return workers
    if supports_distributed_runtime():
        return workers
    raise RuntimeError('Multiple workers are not supported in the current runtime mode. Set WORKERS=1.')


def _resolve_uvicorn_limit_concurrency() -> int | None:
    if settings.worker_connections > 0:
        return settings.worker_connections
    return None


def _mark_running_builds_orphaned_across_namespaces() -> int:
    namespaces = list_namespaces()
    if not namespaces:
        namespaces = [settings.default_namespace]
    count = 0
    for namespace in namespaces:
        token = set_namespace_context(namespace)
        try:
            count += run_db(build_run_service.mark_running_builds_orphaned)
        finally:
            reset_namespace(token)
    return count


async def chat_sweep_loop(stop_event: asyncio.Event) -> None:
    """Periodically sweep expired chat sessions."""
    from modules.chat.sessions import session_store

    while not stop_event.is_set():
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=300)
        if stop_event.is_set():
            break
        try:
            session_store.sweep()
        except Exception as e:
            logger.error('Chat sweep error: %s', e, exc_info=True)


async def engine_cleanup_loop(stop_event: asyncio.Event, manager: ProcessManager) -> None:
    """Periodically check and clean up idle engines."""
    idle_timeout = settings.engine_idle_timeout
    while not stop_event.is_set():
        timeout = max(1.0, manager.next_idle_deadline_seconds(idle_timeout))
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=timeout)
        if stop_event.is_set():
            break
        try:
            cleaned = manager.cleanup_idle_engines()
            if cleaned:
                for analysis_id in cleaned:
                    logger.info(f'Cleaned up idle engine {analysis_id}')
            else:
                logger.debug('No idle engines to clean up')
        except Exception as e:
            logger.error(f'Error in engine cleanup: {e}', exc_info=True)


async def api_worker_heartbeat_loop(stop_event: asyncio.Event, worker_id: str, *, heartbeat_seconds: float = 5.0) -> None:
    while not stop_event.is_set():
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=heartbeat_seconds)
        if stop_event.is_set():
            return
        _heartbeat_api_worker(worker_id)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    logger.info('Starting application...')
    api_worker_id = f'api:{os.getpid()}'
    app.state.api_worker_id = api_worker_id
    app.state.manager = ProcessManager(
        on_snapshot=create_snapshot_notifier(
            asyncio.get_running_loop(),
            persist=lambda namespace, statuses: _persist_engine_snapshot(api_worker_id, namespace, statuses),
        )
    )
    await init_db()
    await asyncio.to_thread(_register_api_worker, api_worker_id)
    await asyncio.to_thread(run_db, ensure_udf_seeds)

    # Start background cleanup task
    stop_event = asyncio.Event()
    ipc_server = await runtime_ipc.start_api_server(listener='api')

    cleanup_task = asyncio.create_task(engine_cleanup_loop(stop_event, app.state.manager))
    chat_sweep_task = asyncio.create_task(chat_sweep_loop(stop_event))
    api_heartbeat_task = asyncio.create_task(api_worker_heartbeat_loop(stop_event, api_worker_id))
    ipc_task = None
    if ipc_server is not None:
        ipc_task = asyncio.create_task(runtime_ipc.serve_api_notifications(ipc_server, stop_event, runtime_ipc.handle_api_payload))

    # Start Telegram bot only if explicitly enabled in settings
    from modules.telegram.bot import telegram_bot

    def _check_bot_enabled(session: Session) -> tuple[bool, str]:
        from modules.settings.service import get_resolved_telegram_settings

        del session
        resolved = get_resolved_telegram_settings()
        enabled = bool(resolved.get('enabled'))
        token = str(resolved.get('token', ''))
        return enabled, token

    from core.database import run_settings_db

    enabled, token = run_settings_db(_check_bot_enabled)
    if enabled:
        telegram_bot.start(token)

    from modules.mcp.routes import get_registry

    get_registry(app)

    yield

    # Stop Telegram bot
    telegram_bot.stop()

    stop_event.set()
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(cleanup_task, timeout=5)
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(chat_sweep_task, timeout=5)
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(api_heartbeat_task, timeout=5)
    if ipc_task is not None:
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(ipc_task, timeout=5)
    await runtime_ipc.stop_api_server(ipc_server, listener='api')
    await close_clients()
    await asyncio.to_thread(_stop_api_worker, api_worker_id)

    # Cleanup compute processes on shutdown
    logger.info('Shutting down compute processes...')
    app.state.manager.shutdown_all()
    logger.info('Application shutdown complete')


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

# Global exception handlers for consistent structured error responses
app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, generic_error_handler)  # type: ignore[arg-type]


@app.middleware('http')
async def namespace_middleware(request: Request, call_next) -> Response:
    token = set_namespace_context(request.headers.get('X-Namespace'))
    try:
        return await call_next(request)
    finally:
        reset_namespace(token)


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.cors_origins_list,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization', 'If-Match', 'X-Client-Id', 'X-Namespace', 'X-Session-Token'],
)


@app.middleware('http')
async def security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '0'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    if not settings.debug:
        response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains'
    return response


app.add_middleware(RequestLoggingMiddleware)

# Include API Routers (prefix already defined in api/router.py)
app.include_router(router)


@app.get('/', response_model=None)
async def root() -> FileResponse | dict[str, str]:
    index_path = frontend_build_dir / 'index.html'

    if settings.prod_mode_enabled and index_path.exists():
        return FileResponse(str(index_path))

    return {'message': 'Welcome to Svelte-FastAPI Template'}


# Health Check Endpoints
@app.get('/health')
async def health() -> dict[str, str]:
    """Basic liveness check - returns 200 if app is running."""
    return {'status': 'healthy', 'service': settings.app_name, 'version': settings.app_version}


@app.get('/health/ready')
async def readiness(request: Request, session: Session = Depends(get_settings_db)) -> JSONResponse:
    """Readiness check - verifies app can handle requests.
    Checks database connectivity, engine manager, and filesystem.
    """
    checks = {}
    is_ready = True

    # Check database
    try:
        session.execute(text('SELECT 1'))
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {e!s}'
        is_ready = False

    # Check engine manager
    try:
        manager = request.app.state.manager
        engine_count = len(manager.list_engines())
        checks['engine_manager'] = 'ok'
        checks['active_engines'] = str(engine_count)
    except Exception as e:
        checks['engine_manager'] = f'error: {e!s}'
        is_ready = False

    # Check filesystem (data directories)
    try:
        paths = namespace_paths(settings.default_namespace)
        checks['upload_dir'] = 'ok' if paths.upload_dir.exists() else 'missing'
        checks['clean_dir'] = 'ok' if paths.clean_dir.exists() else 'missing'
        checks['exports_dir'] = 'ok' if paths.exports_dir.exists() else 'missing'

        if not all(d.exists() for d in [paths.upload_dir, paths.clean_dir, paths.exports_dir]):
            is_ready = False
    except Exception as e:
        checks['filesystem'] = f'error: {e!s}'
        is_ready = False

    status_code = 200 if is_ready else 503
    return JSONResponse(content={'status': 'ready' if is_ready else 'not_ready', 'checks': checks}, status_code=status_code)


@app.get('/health/startup')
async def startup() -> dict[str, str]:
    """Startup probe - quick check for container startup.
    Returns 200 when app is initialized and ready to accept traffic.
    """
    try:
        _ = settings.app_name
        return {'status': 'ready'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@app.get('/{full_path:path}', include_in_schema=False, response_model=None)
async def serve_static_or_index(full_path: str) -> FileResponse:
    if not settings.prod_mode_enabled:
        logger.info('Frontend build not served (development mode or build missing)')
        raise HTTPException(status_code=404, detail='Frontend build not found')

    if full_path.startswith('api/') or full_path == 'api':
        raise HTTPException(status_code=404, detail='Not Found')

    path = frontend_build_dir / full_path
    if path.is_file():
        return FileResponse(str(path))

    fallback_path = frontend_build_dir / '200.html'
    if fallback_path.exists():
        return FileResponse(str(fallback_path))

    index_path = frontend_build_dir / 'index.html'
    if index_path.exists():
        return FileResponse(str(index_path))

    raise HTTPException(status_code=404, detail='File not found')


if __name__ == '__main__':
    import multiprocessing

    import uvicorn

    workers = _guard_runtime_workers(_resolve_uvicorn_workers())

    # Required for multiprocessing 'spawn' context in frozen (Nuitka onefile) executables.
    multiprocessing.freeze_support()

    # In a Nuitka compiled binary there are no source files for uvicorn to watch,
    # so pass the app object directly and disable hot reload.
    # In source mode, the string form 'main:app' is required for --reload to work.
    uvicorn.run(
        app if _NUITKA_COMPILED else 'main:app',
        host='0.0.0.0',
        port=settings.port,
        reload=False if _NUITKA_COMPILED else settings.debug,
        workers=workers,
        limit_concurrency=_resolve_uvicorn_limit_concurrency(),
        log_level=settings.log_level,
        access_log=settings.uvicorn_access_log,
    )
