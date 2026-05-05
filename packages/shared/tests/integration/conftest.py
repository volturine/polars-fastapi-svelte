from __future__ import annotations

import asyncio
import contextlib
import importlib
import threading
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine
from support import base_fixtures
from support.base_fixtures import (
    cleanup_namespace_engines,
    isolate_data_dir,
    mock_file_upload,
    postgres_container,
    pytest_sessionstart,
    sample_analyses,
    sample_analysis,
    sample_csv_file,
    sample_datasource,
    sample_datasources,
    sample_json_file,
    sample_ndjson_file,
    sample_parquet_file,
    temp_upload_dir,
    test_db_session,
)

__all__ = [
    'cleanup_namespace_engines',
    'client',
    'clear_active_build_registry',
    'clear_build_job_hub',
    'clear_build_notification_hub',
    'clear_compute_request_hubs',
    'clear_engine_registry',
    'clear_lock_watchers',
    'isolate_data_dir',
    'isolate_settings_engine',
    'mock_file_upload',
    'postgres_container',
    'pytest_sessionstart',
    'sample_analyses',
    'sample_analysis',
    'sample_csv_file',
    'sample_datasource',
    'sample_datasources',
    'sample_json_file',
    'sample_ndjson_file',
    'sample_parquet_file',
    'temp_upload_dir',
    'test_db_session',
    'test_engine',
    'test_user',
]

if TYPE_CHECKING:
    from modules.auth.models import User


def _register_integration_sqlmodel_metadata() -> None:
    from modules.auth.models import AuthProvider, User, UserSession, VerificationToken
    from modules.chat.models import ChatSession

    from contracts.analysis.models import Analysis, AnalysisDataSource
    from contracts.analysis_versions.models import AnalysisVersion
    from contracts.build_jobs.models import BuildJob
    from contracts.build_runs.models import BuildEvent, BuildRun
    from contracts.datasource.models import DataSource, DataSourceColumnMetadata
    from contracts.engine_instances.models import EngineInstance
    from contracts.engine_runs.models import EngineRun
    from contracts.healthcheck_models import HealthCheck, HealthCheckResult
    from contracts.locks.models import ResourceLock
    from contracts.namespaces.models import RuntimeNamespace
    from contracts.runtime_workers.models import RuntimeWorker
    from contracts.scheduler.models import Schedule
    from contracts.settings_models import AppSettings
    from contracts.telegram_models import TelegramListener, TelegramSubscriber
    from contracts.udf_models import Udf

    del Analysis
    del AnalysisDataSource
    del AnalysisVersion
    del AppSettings
    del AuthProvider
    del BuildEvent
    del BuildJob
    del BuildRun
    del ChatSession
    del DataSource
    del DataSourceColumnMetadata
    del EngineInstance
    del EngineRun
    del HealthCheck
    del HealthCheckResult
    del ResourceLock
    del RuntimeNamespace
    del RuntimeWorker
    del Schedule
    del TelegramListener
    del TelegramSubscriber
    del Udf
    del User
    del UserSession
    del VerificationToken


def _integration_settings_tables() -> list[Any]:
    from modules.auth.models import AuthProvider, User, UserSession, VerificationToken
    from modules.chat.models import ChatSession

    from contracts.engine_instances.models import EngineInstance
    from contracts.namespaces.models import RuntimeNamespace
    from contracts.runtime_workers.models import RuntimeWorker
    from contracts.settings_models import AppSettings

    table_names = {
        AppSettings.__tablename__,
        ChatSession.__tablename__,
        EngineInstance.__tablename__,
        User.__tablename__,
        AuthProvider.__tablename__,
        RuntimeWorker.__tablename__,
        RuntimeNamespace.__tablename__,
        UserSession.__tablename__,
        VerificationToken.__tablename__,
    }
    return [table for table in AppSettings.metadata.sorted_tables if table.name in table_names]


def _reset_integration_settings_state(engine: Engine) -> None:
    from backend_core.settings_store import invalidate_resolved_settings_cache
    from modules.chat.sessions import session_store

    for live in session_store._live.values():
        live.cancel_task()
        live.close_stream()
    session_store._live.clear()

    with engine.begin() as conn:
        for table in reversed(_integration_settings_tables()):
            conn.execute(table.delete())

    invalidate_resolved_settings_cache()


class _InProcessRuntimeAvailabilityProbe:
    def __init__(self, is_alive) -> None:
        self._is_alive = is_alive

    def available(self, *, kind) -> bool:
        from contracts.runtime_workers.models import RuntimeWorkerKind

        if kind is not RuntimeWorkerKind.BUILD_MANAGER:
            return False
        return self._is_alive()


class _InProcessComputeOverrideExecutor:
    def preview_step(self, **kwargs):
        return importlib.import_module('compute_service').preview_step(**kwargs)

    def get_step_schema(self, **kwargs):
        return importlib.import_module('compute_service').get_step_schema(**kwargs)

    def get_step_row_count(self, **kwargs):
        return importlib.import_module('compute_service').get_step_row_count(**kwargs)

    def download_step(self, **kwargs):
        return importlib.import_module('compute_service').download_step(**kwargs)

    def export_data(self, **kwargs):
        return importlib.import_module('compute_service').export_data(**kwargs)


@pytest.fixture(scope='function')
def test_engine(postgres_container):
    from contracts.locks.models import ResourceLock
    from contracts.udf_models import Udf

    del ResourceLock
    del Udf
    schema = f'test_{uuid.uuid4().hex}'
    engine = base_fixtures._schema_engine(postgres_container.url, schema)
    _register_integration_sqlmodel_metadata()
    from core import database

    with engine.begin() as connection:
        connection.execute(text(f'SET search_path TO "{schema}", public'))
        tenant_tables = database._tenant_tables()
        tenant_metadata = tenant_tables[0].metadata if tenant_tables else None
        if tenant_metadata is not None:
            tenant_metadata.create_all(connection, tables=tenant_tables)
    try:
        yield engine
    finally:
        with postgres_container.connect() as pg_connection, pg_connection.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        engine.dispose()


@pytest.fixture(scope='function')
def test_user() -> User:
    from modules.auth.models import User, UserStatus

    now = datetime.now(UTC)
    return User(
        id=uuid.uuid4().hex,
        email='test@example.com',
        display_name='Test User',
        status=UserStatus.ACTIVE,
        email_verified=True,
        has_password=True,
        preferences={},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture(scope='function')
def client(test_db_session, test_user):
    from compute_manager import ProcessManager
    from compute_request_runtime import compute_request_loop
    from engine_notifications import create_snapshot_notifier
    from main import app
    from modules.auth.dependencies import get_current_user
    from runtime_notifications import handle_runtime_payload

    from contracts.runtime import ipc as runtime_ipc
    from core.database import get_db, init_db

    def override_get_db():
        yield test_db_session

    def start_test_runtime() -> tuple[threading.Thread, threading.Event]:
        stop_flag = threading.Event()
        ready_flag = threading.Event()

        def run() -> None:
            async def _runner() -> None:
                await init_db()
                worker_id = f'test-runtime:{uuid.uuid4()}'
                stop_event = asyncio.Event()
                stop_task = asyncio.create_task(asyncio.to_thread(stop_flag.wait))
                stop_task.add_done_callback(lambda _task: stop_event.set())

                manager = ProcessManager(
                    on_snapshot=create_snapshot_notifier(
                        asyncio.get_running_loop(),
                        worker_id=worker_id,
                    )
                )
                ipc_server = await runtime_ipc.start_api_server(listener='job')
                ipc_task = None
                if ipc_server is not None:
                    ipc_task = asyncio.create_task(runtime_ipc.serve_api_notifications(ipc_server, stop_event, handle_runtime_payload))
                request_task = asyncio.create_task(compute_request_loop(stop_event, worker_id=worker_id, manager=manager))
                ready_flag.set()
                try:
                    await stop_event.wait()
                finally:
                    request_task.cancel()
                    await asyncio.gather(request_task, return_exceptions=True)
                    if ipc_task is not None:
                        with contextlib.suppress(asyncio.TimeoutError):
                            await asyncio.wait_for(ipc_task, timeout=5)
                    await runtime_ipc.stop_api_server(ipc_server, listener='job')
                    manager.shutdown_all()
                    stop_flag.set()
                    await asyncio.wait_for(stop_task, timeout=5)

            asyncio.run(_runner())

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        if not ready_flag.wait(timeout=5):
            raise RuntimeError('Timed out starting test compute runtime')
        return thread, stop_flag

    if hasattr(app.state, 'mcp_registry'):
        del app.state.mcp_registry

    app.state.manager = ProcessManager()
    app.state.compute_override_executor = _InProcessComputeOverrideExecutor()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as ac:
        runtime_thread, runtime_stop = start_test_runtime()
        app.state.runtime_availability_probe = _InProcessRuntimeAvailabilityProbe(runtime_thread.is_alive)
        try:
            yield ac
        finally:
            runtime_stop.set()
            runtime_thread.join(timeout=10)
            if hasattr(app.state, 'runtime_availability_probe'):
                del app.state.runtime_availability_probe
            if hasattr(app.state, 'compute_override_executor'):
                del app.state.compute_override_executor
            app.state.manager.shutdown_all()
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True, scope='function')
def clear_lock_watchers():
    from modules.locks.watchers import registry

    asyncio.run(registry.clear())
    yield
    asyncio.run(registry.clear())


@pytest.fixture(autouse=True, scope='function')
def clear_active_build_registry():
    from build_live import registry

    asyncio.run(registry.clear())
    yield
    asyncio.run(registry.clear())


@pytest.fixture(autouse=True, scope='function')
def clear_build_notification_hub():
    from contracts.build_runs.live import hub

    asyncio.run(hub.clear())
    yield
    asyncio.run(hub.clear())


@pytest.fixture(autouse=True, scope='function')
def clear_build_job_hub():
    from contracts.build_jobs.live import hub

    asyncio.run(hub.clear())
    yield
    asyncio.run(hub.clear())


@pytest.fixture(autouse=True, scope='function')
def clear_compute_request_hubs():
    from contracts.compute_requests.live import request_hub, response_hub

    asyncio.run(request_hub.clear())
    asyncio.run(response_hub.clear())
    yield
    asyncio.run(request_hub.clear())
    asyncio.run(response_hub.clear())


@pytest.fixture(autouse=True, scope='function')
def clear_engine_registry():
    from backend_core.engine_live import registry

    asyncio.run(registry.clear())
    yield
    asyncio.run(registry.clear())


@pytest.fixture(autouse=True, scope='function')
def isolate_settings_engine(tmp_path, isolate_data_dir, postgres_container):
    from contracts.settings_models import AppSettings
    from core import database

    schema = f'settings_{uuid.uuid4().hex}'
    engine = base_fixtures._schema_engine(postgres_container.url, schema)
    AppSettings.metadata.create_all(engine, tables=_integration_settings_tables())
    original = database.settings_engine
    database.settings_engine = engine
    database.clear_settings_engine_override()
    try:
        yield engine
    finally:
        database.clear_settings_engine_override()
        _reset_integration_settings_state(engine)
        database.settings_engine = original
        with postgres_container.connect() as pg_connection, pg_connection.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        engine.dispose()
