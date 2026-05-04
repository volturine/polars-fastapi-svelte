from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections.abc import Awaitable, Callable
from typing import Literal

import psycopg
from psycopg import Notify

from core.config import settings

logger = logging.getLogger(__name__)

_CHANNEL = 'runtime_events'
ListenerKind = Literal['api', 'job']
_notify_connection_state: tuple[psycopg.Connection, str] | None = None
_notify_connection_lock = threading.Lock()


def _psycopg_conninfo() -> str:
    return settings.database_url.replace('postgresql+psycopg://', 'postgresql://', 1)


async def start_api_server(listener: ListenerKind = 'api') -> psycopg.Connection | None:
    del listener
    connection = psycopg.connect(_psycopg_conninfo(), autocommit=True)
    connection.execute(f'LISTEN {_CHANNEL}')
    return connection


async def serve_api_notifications(
    server: psycopg.Connection,
    stop_event,
    handler: Callable[[dict[str, object]], Awaitable[None]],
) -> None:
    await _serve_postgres_notifications(server, stop_event, handler)


def _postgres_connection_socket(connection: psycopg.Connection) -> int:
    fileno = getattr(connection, 'fileno', None)
    if callable(fileno):
        socket_fd = fileno()
        if isinstance(socket_fd, int) and socket_fd >= 0:
            return socket_fd
    pgconn = getattr(connection, 'pgconn', None)
    socket_fd = getattr(pgconn, 'socket', None)
    if isinstance(socket_fd, int) and socket_fd >= 0:
        return socket_fd
    raise RuntimeError('Unable to determine Postgres runtime IPC socket')


async def _wait_for_postgres_socket(connection: psycopg.Connection, stop_event) -> bool:
    loop = asyncio.get_running_loop()
    ready = asyncio.Event()
    socket_fd = _postgres_connection_socket(connection)

    def _mark_ready() -> None:
        ready.set()

    loop.add_reader(socket_fd, _mark_ready)
    ready_task = asyncio.create_task(ready.wait())
    stop_task = asyncio.create_task(stop_event.wait())
    try:
        done, pending = await asyncio.wait({ready_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        return ready_task in done
    finally:
        loop.remove_reader(socket_fd)


async def _serve_postgres_notifications(
    connection: psycopg.Connection,
    stop_event,
    handler: Callable[[dict[str, object]], Awaitable[None]],
) -> None:
    while not stop_event.is_set():
        try:
            if not await _wait_for_postgres_socket(connection, stop_event):
                return
            notifications = list(connection.notifies(timeout=0, stop_after=100))
        except (asyncio.CancelledError, psycopg.Error):
            return
        if not notifications:
            continue
        for notify in notifications:
            try:
                payload = json.loads(_notify_payload(notify))
            except json.JSONDecodeError as exc:
                logger.debug('Ignoring malformed Postgres runtime notification: %s', exc)
                continue
            if isinstance(payload, dict):
                await handler(payload)


def _notify_payload(notify: Notify) -> str:
    return notify.payload


async def stop_api_server(server: psycopg.Connection | None, *, listener: ListenerKind = 'api') -> None:
    del listener
    if server is None:
        return
    server.close()


async def handle_api_payload(payload: dict[str, object]) -> None:
    kind = payload.get('kind')
    if kind == 'build':
        from contracts.build_runs.live import BuildNotification, hub as build_hub

        namespace = payload.get('namespace')
        build_id = payload.get('build_id')
        latest_sequence = payload.get('latest_sequence')
        if isinstance(namespace, str) and isinstance(build_id, str) and isinstance(latest_sequence, int):
            await build_hub.publish(
                BuildNotification(
                    namespace=namespace,
                    build_id=build_id,
                    latest_sequence=latest_sequence,
                )
            )
        return
    if kind == 'engine':
        from core.engine_live import registry as engine_registry

        namespace = payload.get('namespace')
        if isinstance(namespace, str):
            await engine_registry.publish_snapshot(namespace, [])
        return
    if kind == 'compute_request':
        from contracts.compute_requests.live import request_hub

        request_hub.publish()
        return
    if kind == 'compute_response':
        from contracts.compute_requests.live import response_hub

        request_id = payload.get('request_id')
        if isinstance(request_id, str):
            response_hub.publish(request_id)
        return
    if kind == 'job':
        from contracts.build_jobs.live import hub as build_job_hub

        build_job_hub.publish()


def notify_api_build(namespace: str, build_id: str, latest_sequence: int) -> None:
    _send_api_message(
        {
            'kind': 'build',
            'namespace': namespace,
            'build_id': build_id,
            'latest_sequence': latest_sequence,
        },
        listener='api',
    )


def notify_api_engine(namespace: str) -> None:
    _send_api_message(
        {
            'kind': 'engine',
            'namespace': namespace,
        },
        listener='api',
    )


def notify_build_job() -> None:
    _send_api_message({'kind': 'job'}, listener='job')


def notify_compute_request(request_id: str) -> None:
    _send_api_message({'kind': 'compute_request', 'request_id': request_id}, listener='job')


def notify_compute_response(request_id: str) -> None:
    _send_api_message({'kind': 'compute_response', 'request_id': request_id}, listener='api')


def _send_api_message(payload: dict[str, object], *, listener: ListenerKind) -> None:
    del listener
    _send_postgres_message(payload)


def _get_notify_connection() -> psycopg.Connection:
    global _notify_connection_state
    conninfo = _psycopg_conninfo()
    with _notify_connection_lock:
        if _notify_connection_state is not None:
            connection, cached_conninfo = _notify_connection_state
            if not connection.closed and cached_conninfo == conninfo:
                return connection
            if not connection.closed:
                connection.close()
        connection = psycopg.connect(conninfo, autocommit=True)
        _notify_connection_state = (connection, conninfo)
        return connection


def _reset_notify_connection() -> None:
    global _notify_connection_state
    with _notify_connection_lock:
        if _notify_connection_state is not None:
            connection, _conninfo = _notify_connection_state
            connection.close()
        _notify_connection_state = None


def _send_postgres_message(payload: dict[str, object]) -> None:
    data = json.dumps(payload)
    try:
        connection = _get_notify_connection()
        connection.execute('SELECT pg_notify(%s, %s)', (_CHANNEL, data))
    except psycopg.Error:
        _reset_notify_connection()
        connection = _get_notify_connection()
        connection.execute('SELECT pg_notify(%s, %s)', (_CHANNEL, data))
