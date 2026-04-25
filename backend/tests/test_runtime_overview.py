from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from core.database import run_db, run_settings_db
from core.namespace import namespace_paths, reset_namespace, set_namespace_context
from modules.build_jobs import service as build_job_service
from modules.build_jobs.models import BuildJob, BuildJobStatus
from modules.compute.core.base import EngineStatusInfo
from modules.engine_instances import service as engine_instance_service
from modules.runtime_workers import service as runtime_worker_service
from modules.runtime_workers.models import RuntimeWorkerKind


def test_runtime_overview_reports_runtime_state(client, monkeypatch) -> None:
    from core.config import settings

    monkeypatch.setattr(settings, 'distributed_runtime_enabled', True, raising=False)
    monkeypatch.setattr(settings, 'database_url', 'postgresql+psycopg://user:pass@host:5432/db', raising=False)

    run_settings_db(
        runtime_worker_service.register_worker,
        worker_id='build-manager-1',
        kind=RuntimeWorkerKind.BUILD_MANAGER,
        hostname='manager-host',
        pid=111,
        capacity=4,
        active_jobs=0,
    )
    run_settings_db(
        runtime_worker_service.register_worker,
        worker_id='build-worker-1',
        kind=RuntimeWorkerKind.BUILD_WORKER,
        hostname='worker-host',
        pid=222,
        capacity=1,
        active_jobs=1,
    )
    run_settings_db(
        engine_instance_service.upsert_engine_status,
        worker_id='build-worker-1',
        namespace='default',
        status=EngineStatusInfo(
            analysis_id='analysis-live',
            status='healthy',
            process_id=4321,
            last_activity=datetime.now(UTC).isoformat(),
            current_job_id='job-live',
            resource_config={'max_threads': 2},
            effective_resources={'max_threads': 2},
            defaults={'max_threads': 2},
        ),
    )

    queued_id = str(uuid.uuid4())
    run_db(build_job_service.create_job, build_id=queued_id, namespace='default')
    leased_id = str(uuid.uuid4())
    run_db(build_job_service.create_job, build_id=leased_id, namespace='default')
    leased = run_db(build_job_service.claim_next_job, worker_id='build-worker-1', lease_seconds=60)
    assert leased is not None
    running = run_db(build_job_service.mark_job_running, leased.id)
    token = set_namespace_context('default')
    try:
        run_db(_expire_job, running.id)
    finally:
        reset_namespace(token)

    response = client.get('/api/v1/runtime/overview')

    assert response.status_code == 200
    body = response.json()
    assert body['mode'] == 'distributed'
    assert body['api']['worker_id'].startswith('api:')
    assert body['api']['version'] == settings.app_version
    assert any(item['id'] == 'build-manager-1' and item['kind'] == 'build_manager' for item in body['workers'])
    assert any(item['id'] == 'build-worker-1' for item in body['workers'])
    assert any(item['analysis_id'] == 'analysis-live' for item in body['engines'])
    assert body['queue']['totals']['queued'] == 1
    assert body['queue']['totals']['running'] == 1
    assert body['queue']['totals']['expired_leases'] == 1
    assert body['queue']['totals']['oldest_queued_age_seconds'] is not None


def test_runtime_overview_reports_single_process_mode(client, monkeypatch) -> None:
    from core.config import settings

    monkeypatch.setattr(settings, 'distributed_runtime_enabled', False, raising=False)
    monkeypatch.setattr(settings, 'database_url', 'sqlite:////tmp/test.db', raising=False)
    monkeypatch.setattr(settings, 'embedded_build_worker_enabled', True, raising=False)

    response = client.get('/api/v1/runtime/overview')

    assert response.status_code == 200
    assert response.json()['mode'] == 'single_process'


def _expire_job(session, job_id: str) -> None:
    job = session.get(BuildJob, job_id)
    assert job is not None
    job.status = BuildJobStatus.RUNNING
    job.lease_expires_at = datetime.now(UTC) - timedelta(seconds=30)
    session.add(job)
    session.commit()


def test_runtime_overview_includes_filesystem_namespaces(client, monkeypatch) -> None:
    from core.config import settings

    monkeypatch.setattr(settings, 'embedded_build_worker_enabled', False, raising=False)
    monkeypatch.setattr(settings, 'distributed_runtime_enabled', False, raising=False)
    namespace_paths('beta')

    response = client.get('/api/v1/runtime/overview')

    assert response.status_code == 200
    namespaces = [item['namespace'] for item in response.json()['queue']['namespaces']]
    assert namespaces == ['default', 'beta']
