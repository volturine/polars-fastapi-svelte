from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import socket
import uuid
from collections.abc import Awaitable, Callable

from core.config import settings
from core.database import run_db, run_settings_db
from core.namespace import list_namespaces, reset_namespace, set_namespace_context
from modules.build_jobs import service as build_job_service
from modules.build_jobs.live import hub as build_job_hub
from modules.build_runs import service as build_run_service
from modules.build_runs.models import BuildRunStatus
from modules.runtime_workers import service as runtime_worker_service
from modules.runtime_workers.models import RuntimeWorkerKind
from modules.scheduler import service as scheduler_service

logger = logging.getLogger(__name__)


async def build_worker_loop(
    stop_event: asyncio.Event,
    worker_id: str,
    run_job: Callable[[str], Awaitable[None]],
    *,
    capacity: int = 1,
    heartbeat_seconds: float = 5.0,
    lease_seconds: int = 30,
    idle_exit_seconds: float | None = None,
    max_jobs: int | None = None,
) -> None:
    _register_worker(worker_id=worker_id, capacity=capacity)
    heartbeat_task = asyncio.create_task(_heartbeat_loop(stop_event, worker_id=worker_id, heartbeat_seconds=heartbeat_seconds))
    last_seen = build_job_hub.version()
    handled_jobs = 0
    try:
        while not stop_event.is_set():
            try:
                handled = await _run_once(worker_id=worker_id, run_job=run_job, lease_seconds=lease_seconds)
                if handled:
                    handled_jobs += 1
                    last_seen = build_job_hub.version()
                    if max_jobs is not None and handled_jobs >= max_jobs:
                        return
                    continue
                if idle_exit_seconds is not None:
                    with contextlib.suppress(TimeoutError):
                        await asyncio.wait_for(stop_event.wait(), timeout=idle_exit_seconds)
                    if stop_event.is_set():
                        continue
                    return
                wait_task = asyncio.create_task(build_job_hub.wait(last_seen))
                stop_task = asyncio.create_task(stop_event.wait())
                heartbeat_sleep = asyncio.create_task(asyncio.sleep(heartbeat_seconds))
                done, pending = await asyncio.wait(
                    {wait_task, stop_task, heartbeat_sleep},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                for task in pending:
                    with contextlib.suppress(asyncio.CancelledError):
                        await task
                for task in done:
                    with contextlib.suppress(asyncio.CancelledError):
                        value = await task
                        if task is wait_task and isinstance(value, int):
                            last_seen = value
            except Exception as exc:
                logger.error('Build worker loop error: %s', exc, exc_info=True)
                await asyncio.sleep(0.1)
    finally:
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task
        _expire_worker_jobs(worker_id)
        _stop_worker(worker_id)


async def _run_once(
    *,
    worker_id: str,
    run_job: Callable[[str], Awaitable[None]],
    lease_seconds: int,
) -> bool:
    job = next_job(worker_id, lease_seconds=lease_seconds)
    if job is None:
        return False

    _heartbeat_worker(worker_id=worker_id, active_jobs=1)
    token = set_namespace_context(job.namespace)
    try:

        def _mark_running(session):
            return build_job_service.mark_job_running(session, job.id)

        run_db(_mark_running)
        renew_stop = asyncio.Event()
        renew_task = asyncio.create_task(
            _renew_job_lease_loop(
                namespace=job.namespace,
                worker_id=worker_id,
                job_id=job.id,
                stop_event=renew_stop,
                lease_seconds=lease_seconds,
            )
        )
        await run_job(job.build_id)
    except Exception as exc:
        logger.error('Build job %s failed: %s', job.build_id, exc, exc_info=True)
        error = str(exc)

        def _mark_failed(session):
            return build_job_service.mark_job_failed(session, job.id, error=error)

        run_db(_mark_failed)
        raise
    finally:
        renew_stop.set()
        with contextlib.suppress(asyncio.CancelledError):
            await renew_task
        _heartbeat_worker(worker_id=worker_id, active_jobs=0)
        reset_namespace(token)

    def _finalize(session):
        run = build_run_service.get_build_run(session, job.build_id)
        if run is None:
            return build_job_service.mark_job_failed(session, job.id, error='Build run missing')
        if run.status == BuildRunStatus.CANCELLED:
            result = build_job_service.mark_job_cancelled(session, job.id)
        elif run.status == BuildRunStatus.COMPLETED:
            result = build_job_service.mark_job_completed(session, job.id)
        elif run.status in {BuildRunStatus.FAILED, BuildRunStatus.ORPHANED}:
            result = build_job_service.mark_job_failed(session, job.id, error=run.error_message)
        else:
            result = build_job_service.mark_job_failed(session, job.id, error=f'Unexpected build status: {run.status.value}')
        scheduler_service.reconcile_schedule_run(session, build_id=job.build_id)
        return result

    run_db(_finalize)
    return True


def next_job(worker_id: str, *, lease_seconds: int = 30):
    namespaces = list_namespaces()
    if not namespaces:
        namespaces = [settings.default_namespace]
    for namespace in namespaces:
        token = set_namespace_context(namespace)
        try:

            def _claim(session):
                return build_job_service.claim_next_job(session, worker_id=worker_id, lease_seconds=lease_seconds)

            job = run_db(_claim)
        finally:
            reset_namespace(token)
        if job is not None:
            return job
    return None


def _register_worker(*, worker_id: str, capacity: int) -> None:
    def _register(session):
        return runtime_worker_service.register_worker(
            session,
            worker_id=worker_id,
            kind=RuntimeWorkerKind.BUILD_WORKER,
            hostname=socket.gethostname(),
            pid=os.getpid(),
            capacity=capacity,
        )

    run_settings_db(_register)


def _heartbeat_worker(*, worker_id: str, active_jobs: int | None = None) -> None:
    def _heartbeat(session):
        return runtime_worker_service.heartbeat_worker(session, worker_id=worker_id, active_jobs=active_jobs)

    run_settings_db(_heartbeat)


def _stop_worker(worker_id: str) -> None:
    def _stop(session):
        return runtime_worker_service.mark_worker_stopped(session, worker_id=worker_id)

    run_settings_db(_stop)


def _expire_worker_jobs(worker_id: str) -> None:
    namespaces = list_namespaces()
    if not namespaces:
        namespaces = [settings.default_namespace]
    for namespace in namespaces:
        token = set_namespace_context(namespace)
        try:

            def _expire(session):
                return build_job_service.expire_worker_jobs(session, worker_id=worker_id)

            run_db(_expire)
        finally:
            reset_namespace(token)


async def _heartbeat_loop(stop_event: asyncio.Event, *, worker_id: str, heartbeat_seconds: float) -> None:
    while not stop_event.is_set():
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=heartbeat_seconds)
        if stop_event.is_set():
            return
        _heartbeat_worker(worker_id=worker_id)


async def _renew_job_lease_loop(
    *,
    namespace: str,
    worker_id: str,
    job_id: str,
    stop_event: asyncio.Event,
    lease_seconds: int,
) -> None:
    interval = max(0.1, lease_seconds / 3)
    while not stop_event.is_set():
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        if stop_event.is_set():
            return

        token = set_namespace_context(namespace)
        try:

            def _renew(session):
                return build_job_service.renew_job_lease(session, job_id, worker_id=worker_id, lease_seconds=lease_seconds)

            run_db(_renew)
        finally:
            reset_namespace(token)


def worker_id() -> str:
    return f'local-worker:{uuid.uuid4()}'
