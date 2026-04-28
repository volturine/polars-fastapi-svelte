from __future__ import annotations

import asyncio
import contextlib
import logging
import multiprocessing
import multiprocessing.process
import os
import signal
import socket
import uuid

from compute_manager import ProcessManager
from engine_live import create_snapshot_notifier
from worker_runtime import build_worker_loop, runtime_namespaces, worker_id as build_worker_id

from contracts.build_jobs.live import hub as build_job_hub
from contracts.runtime import ipc as runtime_ipc
from contracts.runtime_workers.models import RuntimeWorkerKind
from core import (
    build_jobs_service as build_job_service,
    engine_instances_service as engine_instance_service,
    runtime_workers_service as runtime_worker_service,
)
from core.config import settings
from core.database import init_db, run_db, run_settings_db
from core.logging import configure_logging
from core.namespace import reset_namespace, set_namespace_context

logger = logging.getLogger(__name__)
_SPAWN = multiprocessing.get_context('spawn')


def _persist_engine_snapshot(worker_id: str, namespace: str, statuses) -> None:
    def _write(session) -> None:
        engine_instance_service.persist_engine_snapshot(
            session,
            worker_id=worker_id,
            namespace=namespace,
            statuses=list(statuses),
        )

    run_settings_db(_write)
    runtime_ipc.notify_api_engine(namespace)


def _register_manager(worker_id: str) -> None:
    def _register(session) -> None:
        runtime_worker_service.register_worker(
            session,
            worker_id=worker_id,
            kind=RuntimeWorkerKind.BUILD_MANAGER,
            hostname=socket.gethostname(),
            pid=os.getpid(),
            capacity=max(settings.build_worker_max_processes, 0),
        )

    run_settings_db(_register)


def _heartbeat_manager(worker_id: str, active_jobs: int = 0) -> None:
    def _heartbeat(session) -> None:
        runtime_worker_service.heartbeat_worker(session, worker_id=worker_id, active_jobs=active_jobs)

    run_settings_db(_heartbeat)


def _stop_manager(worker_id: str) -> None:
    def _stop(session) -> None:
        runtime_worker_service.mark_worker_stopped(session, worker_id=worker_id)

    run_settings_db(_stop)


def manager_id() -> str:
    return f'build-manager:{uuid.uuid4()}'


def queued_job_count() -> int:
    count = 0
    for namespace in runtime_namespaces():
        token = set_namespace_context(namespace)
        try:
            count += run_db(build_job_service.queued_job_count)
        finally:
            reset_namespace(token)
    return count


async def _manager_heartbeat_loop(stop_event: asyncio.Event, worker_id: str, *, heartbeat_seconds: float = 5.0) -> None:
    while not stop_event.is_set():
        active_children = 0
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=heartbeat_seconds)
        if stop_event.is_set():
            return
        _heartbeat_manager(worker_id, active_jobs=active_children)


def _worker_main() -> None:
    asyncio.run(run_build_worker_process())


async def run_build_worker_process(
    *,
    stop_event: asyncio.Event | None = None,
    idle_exit_seconds: float | None = None,
    max_jobs: int | None = None,
) -> None:
    configure_logging()
    logger.info('Starting build worker process...')
    await init_db()
    local_stop = stop_event or asyncio.Event()
    worker_id = build_worker_id()
    manager = ProcessManager(
        on_snapshot=create_snapshot_notifier(
            asyncio.get_running_loop(),
            persist=lambda namespace, statuses: _persist_engine_snapshot(worker_id, namespace, statuses),
        )
    )

    from build_execution import _run_queued_build_job

    async def run_job(build_id: str) -> None:
        await _run_queued_build_job(manager=manager, build_id=build_id)

    task = asyncio.create_task(
        build_worker_loop(
            local_stop,
            worker_id,
            run_job,
            idle_exit_seconds=idle_exit_seconds,
            max_jobs=max_jobs,
        )
    )
    try:
        await task
    finally:
        local_stop.set()
        if not task.done():
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(task, timeout=5)
        manager.shutdown_all()
        logger.info('Build worker process shutdown complete')


async def run_build_manager_process(*, stop_event: asyncio.Event | None = None) -> None:
    configure_logging()
    logger.info('Starting build worker manager process...')
    await init_db()
    local_stop = stop_event or asyncio.Event()
    ipc_server = await runtime_ipc.start_api_server(listener='job')
    ipc_task = None
    if ipc_server is not None:
        ipc_task = asyncio.create_task(runtime_ipc.serve_api_notifications(ipc_server, local_stop, runtime_ipc.handle_api_payload))
    worker_id = manager_id()
    _register_manager(worker_id)
    heartbeat_task = asyncio.create_task(_manager_heartbeat_loop(local_stop, worker_id))
    children: dict[int, multiprocessing.process.BaseProcess] = {}
    last_seen = build_job_hub.version()
    try:
        while not local_stop.is_set():
            stale = [pid for pid, proc in children.items() if not proc.is_alive()]
            for pid in stale:
                proc = children.pop(pid)
                proc.join(timeout=1)

            queued = await asyncio.to_thread(queued_job_count)
            desired = min(settings.build_worker_max_processes, max(settings.build_worker_min_processes, queued))
            while len(children) < desired:
                proc = _SPAWN.Process(target=_worker_main)
                proc.start()
                children[proc.pid or id(proc)] = proc

            if len(children) >= desired and queued == 0:
                wait_task = asyncio.create_task(build_job_hub.wait(last_seen))
                stop_task = asyncio.create_task(local_stop.wait())
                done, pending = await asyncio.wait({wait_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
                for task in pending:
                    task.cancel()
                for task in pending:
                    with contextlib.suppress(asyncio.CancelledError):
                        await task
                if stop_task in done:
                    await stop_task
                    continue
                with contextlib.suppress(asyncio.CancelledError):
                    value = await wait_task
                    if isinstance(value, int):
                        last_seen = value
                continue

            await asyncio.sleep(0.1)
    finally:
        local_stop.set()
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task
        for proc in children.values():
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=5)
            if proc.is_alive():
                proc.kill()
                proc.join(timeout=5)
        if ipc_task is not None:
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(ipc_task, timeout=5)
        await runtime_ipc.stop_api_server(ipc_server)
        _stop_manager(worker_id)
        logger.info('Build worker manager shutdown complete')


def install_stop_handlers(stop_event: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()

    def _stop() -> None:
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _stop)


async def main() -> None:
    multiprocessing.freeze_support()
    stop_event = asyncio.Event()
    install_stop_handlers(stop_event)
    await run_build_manager_process(stop_event=stop_event)


if __name__ == '__main__':
    asyncio.run(main())
