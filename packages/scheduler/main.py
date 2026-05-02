from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import socket
import uuid

import scheduler_service
from sqlmodel import Session

from contracts.build_jobs.live import hub as build_job_hub
from contracts.runtime import ipc as runtime_ipc
from contracts.runtime_workers.models import RuntimeWorkerKind
from core import runtime_workers_service as runtime_worker_service
from core.config import settings
from core.database import init_db, run_db, run_settings_db
from core.logging import configure_logging
from core.namespace import reset_namespace, set_namespace_context
from core.namespaces_service import list_runtime_namespaces

logger = logging.getLogger(__name__)


async def scheduler_loop(
    stop_event: asyncio.Event,
    worker_id: str,
    *,
    heartbeat_seconds: float = 5.0,
) -> None:
    _register_worker(worker_id=worker_id)
    heartbeat_task = asyncio.create_task(_heartbeat_loop(stop_event, worker_id=worker_id, heartbeat_seconds=heartbeat_seconds))
    last_seen = build_job_hub.version()
    try:
        while not stop_event.is_set():
            handled = await _run_once(worker_id=worker_id)
            if handled:
                last_seen = build_job_hub.version()
                continue
            wait_task = asyncio.create_task(build_job_hub.wait(last_seen))
            stop_task = asyncio.create_task(stop_event.wait())
            sleep_task = asyncio.create_task(asyncio.sleep(settings.scheduler_check_interval))
            done, pending = await asyncio.wait({wait_task, stop_task, sleep_task}, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                with contextlib.suppress(asyncio.CancelledError):
                    value = await task
                    if task is wait_task and isinstance(value, int):
                        last_seen = value
    finally:
        heartbeat_task.cancel()
        await asyncio.gather(heartbeat_task, return_exceptions=True)
        _stop_worker(worker_id)


async def _run_once(*, worker_id: str) -> bool:
    namespaces = _runtime_namespaces()
    handled = False
    for namespace in namespaces:
        token = set_namespace_context(namespace)
        try:
            claimed = await asyncio.to_thread(
                run_db,
                lambda session: _claim_due_schedule_refs(session, worker_id=worker_id),
            )
            if not claimed:
                continue
            handled = True
            for sched_id, datasource_id in claimed:
                try:
                    run_id = await asyncio.to_thread(
                        run_db,
                        lambda session, target_id=sched_id: scheduler_service.enqueue_schedule_run(
                            session,
                            target_id,
                            worker_id=worker_id,
                        ),
                    )
                    logger.info(
                        'Scheduler: enqueued schedule %s as build %s (datasource=%s)',
                        sched_id,
                        run_id,
                        datasource_id,
                    )
                except Exception as exc:
                    logger.error('Scheduler: enqueue failed for schedule %s: %s', sched_id, exc, exc_info=True)
                    await asyncio.to_thread(
                        run_db,
                        lambda session, target_id=sched_id, error=str(exc): scheduler_service.mark_schedule_enqueue_failed(
                            session,
                            target_id,
                            error=error,
                        ),
                    )
        finally:
            reset_namespace(token)
    return handled


def _claim_due_schedule_refs(session: Session, *, worker_id: str) -> list[tuple[str, str]]:
    schedules = scheduler_service.claim_due_schedules(session, worker_id=worker_id)
    return [(schedule.id, schedule.datasource_id) for schedule in schedules]


def _runtime_namespaces() -> list[str]:
    return run_settings_db(list_runtime_namespaces)


def _register_worker(*, worker_id: str) -> None:
    def _register(session):
        return runtime_worker_service.register_worker(
            session,
            worker_id=worker_id,
            kind=RuntimeWorkerKind.SCHEDULER,
            hostname=socket.gethostname(),
            pid=os.getpid(),
            capacity=1,
        )

    run_settings_db(_register)


def _heartbeat_worker(*, worker_id: str) -> None:
    def _heartbeat(session):
        return runtime_worker_service.heartbeat_worker(session, worker_id=worker_id)

    run_settings_db(_heartbeat)


def _stop_worker(worker_id: str) -> None:
    def _stop(session):
        return runtime_worker_service.mark_worker_stopped(session, worker_id=worker_id)

    run_settings_db(_stop)


async def _heartbeat_loop(stop_event: asyncio.Event, *, worker_id: str, heartbeat_seconds: float) -> None:
    while not stop_event.is_set():
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=heartbeat_seconds)
        if stop_event.is_set():
            return
        _heartbeat_worker(worker_id=worker_id)


def scheduler_id() -> str:
    return f'scheduler:{uuid.uuid4()}'


def install_stop_handlers(stop_event: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()

    def _stop() -> None:
        stop_event.set()

    import signal

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _stop)


async def main() -> None:
    configure_logging()
    logger.info('Starting scheduler process...')
    await init_db()
    stop_event = asyncio.Event()
    install_stop_handlers(stop_event)
    ipc_server = await runtime_ipc.start_api_server() if settings.is_postgres else None
    ipc_task = None
    if ipc_server is not None:
        ipc_task = asyncio.create_task(runtime_ipc.serve_api_notifications(ipc_server, stop_event, runtime_ipc.handle_api_payload))
    try:
        await scheduler_loop(stop_event, scheduler_id())
    finally:
        stop_event.set()
        if ipc_task is not None:
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(ipc_task, timeout=5)
        await runtime_ipc.stop_api_server(ipc_server)


if __name__ == '__main__':
    asyncio.run(main())
